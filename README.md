# PRUatcher
## A Python script to watch over your GitHub old Pull Requests
![PRU](./images/pigeon-face-shock-150h.jpg "PRU")

It's deployed as a AWS Lambda and take the following Environment Variables:

Parameter | Description
---------- | -----------
configuration_s3_bucket | S3 bucket where the configuration file can be found
configuration_s3_file | Path to the S3 configuration file
slack_message_icon | Icon that'll be used to send messages on Slack
github_organization | GitHub organization owner of the repositories PRUatcher is going to watch
test_env | Run `Pru` as developer, reading configs from example.json

Stuff like authentication for GitHub and Slack, watched repositories, alert channel and threshold to consider PR's old are all configured by the S3 hosted JSON file defined by the Lambda environment variables `configuration_s3_bucket` and `configuration_s3_file`.

The format of the file is just like `example.json`:

The token is now by organization, so we don rely on a single users. But if you really want or don't have an organization see [documentation](https://github.com/settings/tokens).

It's ok to download the configuration file and re-upload it with your own stuff, just take care not to screw others configurations!

That's it, HTH :)
