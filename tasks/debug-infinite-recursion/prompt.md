# Debug Infinite Recursion

Edit `config.nix`.

The current file has an infinite recursion. Fix it while preserving the intended output:

```nix
{
  name = "nixbench";
  enableDocs = true;
  outputs = [ "nixbench" "manual" ];
}
```

Keep the file as a function that accepts an optional `lib` argument with `optional`.
