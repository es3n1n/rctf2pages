# rctf2pages

**Beware, the code is very janky because I hate JS and I don't want to spend any more time on it than the bare minimum. There is a 100% chance it will not work for your deployment without additional changes because, again, I hate JavaScript. You also have to manually patch the JS bundle.**

JS patches:
- Patch out localStorage.token / localStorage.get('Token').
- Patch out logout/profile/buttons.
- Patch out flag submit block.
- Patch out filters.
- Patch leaderboard-now:
```js
({
  division: e,
  limit: t = 100,
  offset: r = 0
}) => De('GET', `/leaderboard/now-${e || "all"}-${t}-${r}`, {})
```
- Patch leaderboard-graph:
```js
({
  division: e
}) => De('GET', `/leaderboard/graph-${e || "all"}-10`, {})
```
- Remove "Register now" button from the main page.

Links rot, which would be especially sad when you have a beautifully themed
RCTF website :(. None of the existing RCTF archival technologies archive the
entire website and keep it browsable; in most cases, they only archive the
handouts and the challenge descriptions.

This is why we created rctf2pages. Github Pages can now host a static version
of a RCTF site long after the CTF event is over.

Challenges that need special hosting requirements, such as netcat-based
challenges, are not in scope of this project, unfortunately. Though I guess
you can try to figure the challenges out from the given handouts (if any) or
public releases of challenge source code repositories (if available).

### Examples

A ~~picture~~ live site is worth a thousand words:

- Malta CTF [Quals 2025](https://quals.2025.ctf.mt/)
- (Feel free to send us a PR and add yours here)

## Usage

It's mostly just bash, JavaScript and Python. To install JS dependencies:

```bash
$ npm install
```

This tool is separated into many stages, each does a different operation.
To see usage information:

```bash
$ ./stage
Usage: ./stage [stage number]
Stages:

  ./stage 00            init
  ./stage 01            scrape
  ./stage 02            json_resolve
[...]
```

Each stage will operate on the git repository, but will not push unless
otherwise specified. To see what each stage does check `run.sh` for the
commit title, and `stage.sh` for the executed commands.

### GitHub Pages Setup

Follow [GitHub documentation](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site).
In particular, you need to setup a `CNAME` DNS record on your DNS provider to
`<user>.github.io` or `<organization>.github.io`. You also need to set the
"Custom domain" setting under GitHub Pages settings for the repository.

### Known issues

- `api/v1/challs/[challenge]/solves?limit=10&offset=10` is not patched to be saved as solves-10-10 (something i will do by the time i will be archiving next rctf)

## License

Copyright 2022 es3n1n \
Copyright 2022 SIGPwny \ 
Copyright 2022 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

&emsp; http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
