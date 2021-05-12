# all hooks we need to run per extension

declare -A hooks
hooks=([md]=mdformat [py]=black,flake8,isort,pydocstyle)


# fetch the list of modified files from git itself
# grep by extension defined in the associative array
# if hook actions are required increment the error code before making them happen
# issues with bash variable and nested loops in subshells asked for a lock file

for e in ${!hooks[@]}; do
  git diff --name-only --diff-filter=ACM | grep ".$e$" | while read f; do
    for h in $(sed 's/,/ /g' <<< ${hooks[$e]}); do
      echo -e "\n\e[1m$h:\e[0m"

      o=$(grep -v "^\s*#" ~/hooks.y*ml | grep --after-context=3 "^$h:")
      cmd=$(awk '$1=="cmd:" {$1="";print$0}' <<< $o | sed 's/^ //g')
      flags=$(awk '$1=="flags:" {$1="";print$0}' <<< $o | sed 's/^ //g')
      check=$(awk '$1=="check:" {$1="";print$0}' <<< $o | sed 's/^ //g')

      if ! $cmd $check $flags "$f" &>/dev/null; then
        $cmd $flags "$f" | sed 's/^/ /g'
        > .commitlock
        echo -e "\e[97;41m$cmd $flags\e[39;0m"
      else
        echo -e "\e[97;42m$cmd $flags\e[39;0m"
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
