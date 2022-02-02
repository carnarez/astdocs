#!/bin/bash

export TERM=xterm-256color

# all hooks we need to run, organised by extension
# they will be run in the order provided

declare -A hooks
hooks=([md]=mdformat [py]=black,flake8,isort,mypy,pydocstyle)


# grep by extension defined in the associative array
# fetch the list of modified files corresponding to this extension from git itself
# if hook actions are required increment the error code before making them happen
# issues with bash variables and nested loops in subshells asked for a lock file

for e in "${!hooks[@]}"; do
  for h in ${hooks[$e]//,/ }; do

    # list files from this commit; if an index.lock is present we expect it to be due to
    # modified but manually unstaged files to be part of the commit
    if [ -f .git/index.lock ]; then
        s=$(git diff --cached --diff-filter=ACM --name-only | grep -e "\.$e$" | tr "\n" " ")
        u=$(git diff --diff-filter=ACM --name-only | grep -e "\.$e$" | tr "\n" " ")
        files=$(echo "$s $u" | xargs -n1 | sort -u | xargs)
    else
        files=$(git commit --short | grep -E "^[ACM]" | grep -e "\.$e$" | awk '{printf" %s",$2}')
    fi

    # check and apply hook action
    if [ -n "$files" ] && [ "$files" != " " ]; then
      echo -e "\n$(tput bold)$h:$(tput sgr0)"

      obj=$(grep -v "^\s*#" /usr/share/pre-commit/hooks.y*ml | grep --after-context=3 "^$h:")
      cmd=$(awk '$1=="cmd:" {$1="";print$0}' <<< "$obj" | xargs)
      flags=$(awk '$1=="flags:" {$1="";print$0}' <<< "$obj")
      check=$(awk '$1=="check:" {$1="";print$0}' <<< "$obj")

      if ! eval "$cmd $check $flags $files" &>/dev/null; then
        eval "$cmd $flags $files" 2>&1 | sed 's/^/ /g'
        touch .commitlock
        echo -e "$(tput setab 1)$cmd$flags$(tput sgr0)"
      else
        echo -e "$(tput setab 2)$cmd$flags$(tput sgr0)"
      fi
    fi

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
