sed -n '/A few/,/# Snippets/p' README.md > tmp1
python with_toc.py | sed 's/^#/##/g' > tmp2
cat tmp? > README.md
rm tmp?
