export TERM=xterm-256color

# all hooks we need to run, organised by extension
# they will be run in the order provided

declare -A hooks
hooks=([md]=mdformat [py]=black,flake8,isort,mypy,pydocstyle)


# fetch the list of modified files from git itself
# grep by extension defined in the associative array
# if hook actions are required increment the error code before making them happen
# issues with bash variables and nested loops in subshells asked for a lock file



for e in ${!hooks[@]}; do
  git diff --name-only --diff-filter=ACM | sort | uniq | grep ".$e$" | while read f; do
    for h in $(sed 's/,/ /g' <<< ${hooks[$e]}); do
      echo -e "\n$(tput bold)$h:$(tput sgr0)"

      o=$(grep -v "^\s*#" ~/hooks.y*ml | grep --after-context=3 "^$h:")
      cmd=$(awk '$1=="cmd:" {$1="";print$0}' <<< $o | xargs)
      flags=$(awk '$1=="flags:" {$1="";print$0}' <<< $o)
      check=$(awk '$1=="check:" {$1="";print$0}' <<< $o)

      if ! $cmd $check $flags "$f" &>/dev/null; then
        $cmd $flags "$f" 2>&1 | sed 's/^/ /g'
        > .commitlock
        echo -e "$(tput setab 1)$cmd$flags$(tput sgr0)"
      else
        echo -e "$(tput setab 2)$cmd$flags$(tput sgr0)"
      fi

    done
  done
done


# if lock file is present return an error code and the commit will be aborted
# running things for a second time should fix it

if [ -f .commitlock ]; then
  rm .commitlock
  echo -e "\nSome files need fixing, cancelling the commit."
  exit 1
else
  echo -e "\nAll green, commit summary:"
  exit 0
fi
