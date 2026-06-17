# /diff-review

Interactive code review using [vibediff](https://github.com/malvex/vibediff).

## What it does

1. Launches vibediff, which opens a browser-based diff viewer for the current git changes
2. You review the diff and leave inline comments in the UI
3. When you say "done", Claude collects the comments and addresses each one
4. Say "abort" to kill vibediff and discard comments

## Prerequisites

- [vibediff](https://github.com/malvex/vibediff) installed:
  ```bash
  brew install malvex/tap/vibediff
  ```

## Usage

```
/diff-review
```

No arguments needed — vibediff picks up the current git diff automatically.
