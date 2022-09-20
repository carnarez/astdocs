# render markdown to html

FROM python:slim as render

WORKDIR /usr/src

COPY build .
COPY content .

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends --yes git \
 && pip install -U pip \
 && pip install -r requirements.txt \
 && find . -name "*.md" | while read f; do \
      mkdir -p /var/www/`dirname $f`; \
      python render.py $f > /var/www/`echo $f | sed 's/README/index/g;s/.md$/.html/g'`; \
    done


# minify everything in place

FROM node:alpine as bundle

WORKDIR /var/www

COPY --from=render /var/www .

COPY static .

RUN npm config set update-notifier false \
 && npm install --global --no-audit --no-fund autoprefixer clean-css-cli html-minifier postcss-cli | grep -v ^$ \
 && find . -name "*.css" | while read f; do \
      postcss $f --replace --use autoprefixer; \
      cleancss --output $f $f; \
    done \
 && find . -name "*.html" | while read f; do \
      html-minifier --collapse-boolean-attributes \
                    --collapse-whitespace \
                    --output $f \
                    --minify-css true \
                    --minify-js true \
                    --remove-attribute-quotes \
                    --remove-comments \
                    --remove-empty-attributes \
                    --remove-optional-tags \
                    --remove-redundant-attributes \
                    --remove-script-type-attributes \
                    --remove-style-link-type-attributes \
                    --use-short-doctype \
                    $f; \
    done


# create an entrypoint.sh to trap the httpd process

FROM busybox

RUN addgroup -S www \
 && adduser -DHS -G www -s /bin/sh www \
 && touch /etc/httpd.conf \
 && echo "/bin/httpd -c /etc/httpd.conf -f -h /var/www -p 0.0.0.0:80" > /usr/sbin/entrypoint.sh \
 && chmod +x /usr/sbin/entrypoint.sh

WORKDIR /var/www

COPY --from=bundle /var/www .

COPY static .

USER www

ENTRYPOINT ["/bin/sh", "-c", "/usr/sbin/entrypoint.sh"]
