ASTDOCS_SPLIT_BY=m python3 process.py | csplit -qz - '/^%%%BEGIN/' '{*}'

grep -v '^%%%BEGIN' xx00 > README.md
rm xx00

for f in xx??; do
  path=$(grep -m1 '^%%%BEGIN' $f | sed -r 's|%%%.* (.*)|\1|g;s|\.|/|g')
  mkdir -p "docs/$(dirname $path)"
  grep -v '^%%%BEGIN' $f > "docs/$path.md"  # double quotes are needed
  rm $f
done

rm docs/*/astdocs.md  # cleanup
