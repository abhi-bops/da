# Introduction

`da` is a custom python script that I have been using, tinkering for my daily use to analyse data. The original tools that I used to do analysis were bash commands like awk, grep, sort ... . `da` offers me to add some more analysis actions and additional features to apply on the output results. It attempts to be integrate into the workflow of using bash pipes to chain actions on data.

The usage is not yet simple and lacks documenation, as the consumer of the code has been mostly been me, so I ended up using what seemed like the best choices at the time. So it is in-a-way ended up being a playground for me to learn python and use them everyday. The documentation and code clean up is pending, which I plan to update very soon in a hope it will be useful to others too.

The inspiration to write `da` came from the amazing tool `visidata` from https://github.com/saulpw/visidata . However, I wrote `da` to be able to be a simple script that I can copy over to a remote machine and execute without having to worry about installing python modules. So, most of the functionality (except graphing, and fanc-ier output) works using the built-in python modules.
