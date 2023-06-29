echo "Begin scraping slack........................................"

git clone https://github.com/iulspop/slack-web-scraper.git slack-tmp
cd slack-tmp && mkdir -p cookies
cp $1 cookies/slack-session-cookies.json
cp $2 .
npm install
npm run collect
npm run parse
cp slack-data/*.json ../slack-data
cd -
rm -rf slack-tmp/

echo "............................................................"
echo "Slack scrape complete."