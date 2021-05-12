# the various linters/checkers to run
# each will be run on each file individually

# https://pycqa.github.io/isort/docs/configuration/options/
isort="isort --multi-line=3 --profile=black --show-files"

# https://black.readthedocs.io/en/stable/usage_and_configuration/the_basics.html
black="black -v"

# https://flake8.pycqa.org/en/latest/user/options.html
# https://flake8.pycqa.org/en/latest/user/error-codes.html  
flake8="flake8 --max-doc-length=88 --max-line-length=88"

# http://www.pydocstyle.org/en/stable/usage.html
pydoc="pydocstyle --convention=numpy"

# https://mdformat.readthedocs.io/en/stable/users/style.html
mdfmt="mdformat --wrap=88"


# fetch the list of modified files
# making sure we handle spaces in filenames properly
# loop is redundant but clear and fast

for hook in "$isort" "$black" "$flake8" "$pydoc"; do
  echo $hook
  git diff --name-only --diff-filter=ACM | grep '.py$' | while read f; do
    $hook "$f"
  done
done

for hook in "$mdfmt"; do
  echo $hook
  git diff --name-only --diff-filter=ACM | grep '.md$' | while read f; do
    $hook "$f"
  done
done
