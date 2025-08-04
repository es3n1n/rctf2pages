const assert = require('node:assert');
const fs = require('node:fs');
const http = require('http'); ;
const https = require('https'); ;
const path = require('node:path');
const url = require('node:url');

const puppeteer = require('puppeteer');

function splitOnce(str, sep) {
  const pos = str.indexOf(sep);
  return pos === -1 ? [str]
      : [str.slice(0, pos), str.slice(pos + sep.length)];
}

const sleep = (timeout) => {
  return new Promise((resolve) => {
    setTimeout(resolve, timeout);
  });
};

// A promise with resolve & reject method on it
const deferred = () => {
  let resolve;
  let reject;

  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });

  promise.resolve = resolve;
  promise.reject = reject;
  return promise;
};

class HeartBeat {
  constructor() {
    this.resolved = false;
    this.deferred = deferred();
    this.timer = undefined;
  }

  heartbeat(timeout) {
    // if (this.resolved) {
    //   throw new Error('Already timed out');
    // }
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = undefined;
    }
    if (timeout >= 0) {
      this.timer = setTimeout(() => {
        // assert(!this.resolved);
        this.deferred.resolve();
        this.resolved = true;
      }, timeout);
    }
  };

  async wait() {
    await this.deferred;
  }
}

class WaitAll {
  constructor() {
    this.waitlist = new Set();
    this.deferred = deferred();
  }

  add(promise) {
    this.waitlist.add(promise);

    promise.then(() => {
      this.waitlist.delete(promise);
      if (!this.waitlist.size) {
        this.deferred.resolve();
      }
    }, (err) => {
      this.deferred.reject(err);
    });
  }

  async wait() {
    await this.deferred;
  }
}

class PageHandler {
  constructor(parent, browser, pageUrl) {
    this.parent = parent;
    this.browser = browser;
    this.pageUrl = pageUrl;

    this.redirectedTargets = new Map();
    this.pendingRequests = new Set();
    this.browseCompleted = undefined;
  }

  async setHooks(page) {
    // Sometimes static files don't get requestfinished somehow.
    // - If all requests done, timeout 250ms
    // - If only irrelevant files remaining, timeout 10s
    // - Else timeout infinity.
    const heartbeat = () => {
      let timeout;
      if (!this.pendingRequests.size) {
        timeout = 250;
      } else if (Array.from(this.pendingRequests).every((requestUrl) => {
        return !requestUrl.startsWith(this.parent.origin) ||
            this.parent.completedPaths.has(this.parent.urlToPath(requestUrl));
      })) {
        timeout = 10000;
      } else {
        timeout = -1;
      }
      this.browseCompleted.heartbeat(timeout);
    };

    page.on('request', (request) => {
      const requestUrl = request.url();

      if (requestUrl.startsWith('data:')) {
        return;
      }

      this.pendingRequests.add(requestUrl);
      heartbeat();
    });

    page.on('requestfailed', (request) => {
      const requestUrl = request.url();

      this.pendingRequests.delete(requestUrl);
      heartbeat();

      if (requestUrl.startsWith(this.parent.origin)) {
        this.parent.completedPaths.add(this.parent.urlToPath(requestUrl));
      }
    });

    page.on('requestfinished', async (request) => {
      await page.evaluate((tok) => {
        localStorage.setItem('token', tok);
      }, this.parent.token);
      const requestUrl = request.url();
      const response = request.response();
      const originRedirect = this.redirectedTargets.get(requestUrl);

      this.pendingRequests.delete(requestUrl);
      heartbeat();

      if (requestUrl.startsWith(this.parent.origin)) {
        this.parent.completedPaths.add(this.parent.urlToPath(requestUrl));
      }

      if (originRedirect || requestUrl.startsWith(this.parent.origin)) {
        const status = response.status();

        if (requestUrl.includes('solves') && status != 200) {
          console.log(requestUrl);
          assert(false);
        }

        if ((status >= 200 && status < 300) ||
            requestUrl === `${this.parent.origin}404`) {
          let url;
          if (!originRedirect || requestUrl.startsWith(this.parent.origin)) {
            url = new URL(requestUrl);
          } else {
            url = new URL(originRedirect);
          }
          let filepath = this.parent.urlToPath(`${url.origin}${url.pathname}`);

          if (filepath.includes('api/v1/leaderboard/now')) {
            filepath += `-${url.searchParams.get("division") || "all"}`
            filepath += `-${url.searchParams.get("limit")}`
            filepath += `-${url.searchParams.get("offset")}`
          } else if (filepath.includes('api/v1/leaderboard/graph')) {
            filepath += `-${url.searchParams.get("division") || "all"}`
            filepath += `-${url.searchParams.get("limit")}`
          } else if (/\/api\/v1\/challs\/([^/]+)\/solves$/.test(filepath)) {
            filepath += `-${url.searchParams.get("limit") || "0"}`
            filepath += `-${url.searchParams.get("offset") || "0"}`
          } else if (filepath.includes('api/v1/challs')) {
            this.parent.challsResponse = JSON.parse(await response.text());
          }

          if (filepath.includes('?') || filepath.includes('&') || filepath.includes('undefined')) {
            console.log(filepath);
            assert(false);
          }

          // File extension added because sometimes an URL needs to be both a
          // page and a directory...
          if (!filepath.endsWith('.json') &&
              response.headers()['content-type'].includes('application/json')) {
            filepath += '.json';
          }
          if (!filepath.endsWith('.html') && !filepath.includes('?') &&
              response.headers()['content-type'].includes('text/html')) {
            filepath += '.html';
          }

          if (!this.parent.completedDownloads.has(filepath)) {
            this.parent.completedDownloads.add(filepath);

            await fs.promises.mkdir(path.dirname(filepath), {recursive: true});

            let buffer;
            try {
              buffer = await response.buffer();
            } catch (err) {
              console.log(requestUrl, filepath);
              console.log(err);
              throw err;
            }

            await fs.promises.writeFile(filepath, buffer);
            console.log('done:', filepath);
          }

          if (originRedirect && requestUrl.startsWith(this.parent.origin)) {
            // not handling internal -> internal redirects
            assert(false);
          }
        } else if (status >= 300 && status < 400) {
          const next = new url.URL(
              response.headers()['location'], requestUrl).href;

          this.redirectedTargets.set(next, originRedirect || requestUrl);
        }
      }
    });

    // consider pages with text/event-stream failed since they never finish
    // responding and cannot be archived.
    // https://github.com/sigpwny/ctfd2pages/issues/13#issuecomment-1621129029
    page.on('response', (response) => {
      const request = response.request();
      const requestUrl = request.url();

      let contenttype = response.headers()['content-type'];
      if (!contenttype) {
        return;
      }
      if (contenttype.includes(';')) {
        contenttype = contenttype.substring(0, contenttype.indexOf(';'));
      }

      if (contenttype === 'text/event-stream') {
        if (requestUrl.startsWith(this.parent.origin)) {
          this.pendingRequests.delete(requestUrl);
          heartbeat();

          this.parent.completedPaths.add(this.parent.urlToPath(requestUrl));
        }
      }
    });
  }

  async handleSpecials(page) {
    if (this.pageUrl === `${this.parent.origin}`) {
      // Puppeteer headless don't fetch favicon
      const favicon = await page.$eval('link[rel*=\'icon\']',
          (e) => e.href);
      this.parent.allHandouts.add(favicon);
    } else if (this.pageUrl == `${this.parent.origin}scores`){
      const page_buttons = await page.$$('div[class~=\'pagination-item\']');
      const pages_count_def = await page_buttons[page_buttons.length - 2].evaluate(el => parseInt(el.innerText));
      const teams_at_least = 100 * pages_count_def

      let divisions;
      try {
        divisions = await page.$eval('select[name=\'division\']',
            (e) => Array.from(e.childNodes).map((x) => x.value) );
      } catch(err) { // no divisions
        divisions = ['all'];
      }
      const page_sizes = await page.$eval('select[name=\'pagesize\']', 
          (e) => Array.from(e.childNodes).map((x) => parseInt(x.value)) );
      
      for (const division of divisions) {
        for (const size of page_sizes) {
          const pages_count = teams_at_least / size;
          for (let page = 0; page < pages_count; ++page) {
            this.parent.pushpage(`${this.parent.origin}scores?page=${page + 1}&division=${division}&pageSize=${size}`)
          }
        }
      }
    } else if (this.pageUrl === `${this.parent.origin}challs`) {
      const frames = await page.$$('.frame');
      const chal_frames = frames.slice(2);

      for (const chal_frame of chal_frames) {
        const title = await chal_frame.evaluate((el) => (el.getElementsByClassName('frame__title')[0].innerText));
        const solves_pts = (await chal_frame.evaluate((el) => (el.getElementsByClassName('u-text-right')[0].innerText))).split(' / ').map((x) => parseInt(x.split(' ')[0]));

        let [chall_category, chall_name] = splitOnce(title, '/');
        let challenge = this.parent.resolveChallenge(chall_category, chall_name);
        if (!challenge) {
          throw Error(`Unable to resolve ${chall_category}/${chall_name}`);
        }

        for (var i = 0; i < solves_pts[0]; i += 10) {
          this.parent.pushpage(`${this.parent.origin}api/v1/challs/${encodeURIComponent(challenge.id)}/solves?limit=10&offset=${i}`);
        }

        const attachments = await chal_frame.evaluate(
          (el) => Array.from(el.getElementsByClassName('tag')).map((x) => Array.from(x.getElementsByTagName('a')).map((y) => y.href))
        );
        for (const attachment of attachments) {
          this.parent.allHandouts.add(attachment[0]);
        }
      }
    }
  }

  async run() {
    const page = await this.browser.newPage();
    this.browseCompleted = new HeartBeat();

    // Allow fetching large resources
    // https://github.com/sigpwny/ctfd2pages/issues/13#issuecomment-1621091707
    // https://github.com/puppeteer/puppeteer/issues/1599#issuecomment-355473214
    // https://github.com/puppeteer/puppeteer/issues/6647#issuecomment-1610949415
    page._client().send('Network.enable', {
      maxResourceBufferSize: 100 << 20,
      maxTotalBufferSize: 200 << 20,
    });

    await this.setHooks(page);

    console.log('visiting:', this.pageUrl);
    await page.goto(this.pageUrl);

    await this.browseCompleted.wait();

    const links = await page.$$eval('a',
        (l) => l.map((e) => e.href));

    for (let link of links) {
      if (!link.startsWith(this.parent.origin)) {
        continue;
      }

      link = new url.URL(link);
      link.hash = '';
      link = link.href;

      this.parent.pushpage(link);
    }

    // Return this promise, then async handle special pages
    this.parent.waitallnav.add((async () => {
      await this.handleSpecials(page);

      // Give it 10 seconds to download any remaining resources
      await sleep(10000);

      page.close();
    })());
  }
}

class Rctf2Pages {
  constructor(origin, basepath, token) {
    this.origin = origin;
    this.basepath = basepath;
    this.token = token;

    this.toVisit = [];
    this.challsResponse = {};
    this.visited = new Set();
    this.completedDownloads = new Set();
    this.completedPaths = new Set();
    this.allHandouts = new Set();
    this.waitallnav = new WaitAll();
  }

  resolveChallenge(category, name) {
    return this.challsResponse.data.find(element => {
      return element.name == name && element.category == category;
    });
  }

  urlToPath(requestUrl) {
    let filepath = '/'    
    if (!requestUrl.startsWith(this.origin)) {
      console.warn(`${requestUrl} does not start with ${this.origin}!!!!!!!, ghetto-ing`);
      const parts = requestUrl.split('/');
      filepath += parts.slice(3).join('/');
    } else {
      filepath += requestUrl.substring(this.origin.length);
    }
  
    filepath = filepath.replace(/\?d=[0-9a-f]{8}$/, '');
    filepath = filepath.replace(/\?_=[0-9]+$/, '');
    if (filepath.endsWith('/')) {
      filepath += 'index.html';
    }
    filepath = path.join(this.basepath, `./${filepath}`);
    return filepath;
  };

  downloadFile(requestUrl, filepath) {
    const urlobj = new url.URL(requestUrl);
    let handlerModule;

    if (urlobj.protocol === 'http:') {
      handlerModule = http;
    } else if (urlobj.protocol === 'https:') {
      handlerModule = https;
    } else {
      assert(false);
    }

    return new Promise((resolve, reject) => {
      handlerModule.get(requestUrl, (response) => {
        const status = response.statusCode;

        if (status >= 200 && status < 300) {
          let fd = fs.openSync(filepath, 'w');

          response.on('data', (chunk) => {
            fs.writeSync(fd, chunk);
          });
          response.on('end', () => {
            fs.closeSync(fd);
            fd = undefined;
            resolve();
          });
        } else if (status >= 300 && status < 400) {
          const next = new url.URL(response.headers.location, requestUrl).href;
          this.downloadFile(next, filepath).then(resolve, reject);
        } else {
          reject(new Error(status));
        }
      }).on('error', (err) => {
        reject(err);
      });
    });
  };

  pushpage(pageUrl) {
    if (this.visited.has(pageUrl)) {
      return;
    }

    this.toVisit.push(pageUrl);
    this.visited.add(pageUrl);
  }

  async poppage(browser) {
    const pageUrl = this.toVisit.shift();
    await new PageHandler(this, browser, pageUrl).run();
  }

  async run() {
    const browser = await puppeteer.launch({headless: 'new'});

    this.pushpage(this.origin);
    this.pushpage(`${this.origin}404`);

    while (this.toVisit.length) {
      console.log(this.toVisit.length, 'pending pages');
      await this.poppage(browser);
    }

    await this.waitallnav.wait();

    console.log('processing files')
    for (const handout of this.allHandouts) {
      const filepath = this.urlToPath(handout);
      if (!this.completedDownloads.has(filepath)) {
        await fs.promises.mkdir(path.dirname(filepath), {recursive: true});
        await this.downloadFile(handout, filepath);
        console.log('done:', filepath);
      }
    }

    browser.close();
  }
}

const main = async function() {
  const args = process.argv.slice(2);

  if (args.length !== 3) {
    console.error(
        `Usage: ${process.argv[0]} ${process.argv[1]} [origin] [path]`);
    console.error(
        `Example: ${process.argv[0]} ${process.argv[1]} https://quals.2025.ctf.mt/ 2025/`);
    return 1;
  }

  let [origin, basepath, token] = args;
  if (!origin.endsWith('/')) {
    origin += '/';
  }
  await new Rctf2Pages(origin, basepath, token).run();

  return 0;
};

if (require.main === module) {
  main().then(process.exit);
}
