#!/usr/bin/env bash
set -eu
cd -- "$(dirname -- "$0")"
load_path=ga_checkpoint.bin
save_path=
load_requested=0
save_explicit=0
for arg in "$@"; do
  case "$arg" in
    --load) load_requested=1 ;;
    --load=*) load_requested=1; load_path=${arg#--load=} ;;
    --save=*) save_explicit=1; save_path=${arg#--save=} ;;
  esac
done
if [ "$save_explicit" = 0 ]; then save_path=$load_path; fi
if [ -z "$load_path" ] || [ -z "$save_path" ]; then
  echo "Checkpoint paths must not be empty." >&2
  exit 1
fi
if [ "$load_requested" = 1 ] && [ ! -f "$load_path" ] && [ ! -f "$load_path.bak" ]; then
  echo "Checkpoint and backup not found: $load_path" >&2
  exit 1
fi
nim c -d:release --threads:on --gc:orc -o:at_jev_checked at_jev.nim
./at_jev_checked --filter-test
./at_jev_checked --bottleneck-test
./at_jev_checked --refinement-test
./at_jev_checked --fusion-test
./at_jev_checked --generation-index-test
./at_jev_checked --regression-test
./at_jev_checked --self-test
python3 -m unittest discover -s . -p 'test_*.py'
backup_dir=
backup_checkpoint() {
  source_path=$1
  label=$2
  for file in "$source_path" "$source_path.bak" "$source_path.model" "$source_path.jev_progress.csv" "$source_path.jev_progress.csv.config.json"; do
    if [ -f "$file" ]; then
      if [ -z "$backup_dir" ]; then backup_dir=$(mktemp -d ./pre_run_backup.XXXXXX); fi
      mkdir -p -- "$backup_dir/$label"
      cp -p -- "$file" "$backup_dir/$label/"
    fi
  done
}
if [ "$load_requested" = 1 ]; then backup_checkpoint "$load_path" input; fi
if [ "$load_requested" = 0 ] || [ "$save_path" != "$load_path" ]; then
  backup_checkpoint "$save_path" output
fi
if [ -n "$backup_dir" ]; then echo "Previous files preserved: $backup_dir"; fi
exec ./at_jev_checked "$@"
