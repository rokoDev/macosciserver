# CIServer

This is continious integration server for processing requests from github.com.
Server written in ruby so to install it on your Mac follow this guide:
https://github.com/monfresh/install-ruby-on-macos
After installing ruby you also need to install "sinatra" and "octokit".

If you are behind NAT - you need to run ngrok ( https://ngrok.com ): $ ngrok http 4567
Just after run ngrok printout reference(similar to: http://633a03453ce3.ngrok.io) by
which github can access your host. You should go to your github project' settings ->
Webhooks and put this reference to "Payload URL" field followed by "/event_handler".
"Payload URL" should be like: http://633a03453ce3.ngrok.io/event_handler

In config.json file you can set branch name and whether pull requests and pushes to
this branch should be processed.

Also you must have private_config.json (keep it in secret!) with similar content:

{
    "CIWorkPath": "path to directory where source code and builds resides",
    "GIT_TOKEN": "40 symbols token"
}

In order to get GIT_TOKEN go to your github profile -> Settings -> Developer settings ->
Personal access tokens and press "Generate new token"


To run CIServer: $ rackup -p 4567 config.ru