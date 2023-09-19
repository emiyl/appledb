const apple_data = require('apple-data')
const octokit = require('octokit')
const fs = require('fs')
const path = require('path')

async function update_credits() {
    this.async()

    const hd_credits = await apple_data.getData('credits')
    const apple_data_credits = hd_credits['repositories']['hack-different/apple-knowledge']

    const credits_file = path.join(__dirname, '..', 'credits.json')

    let client = new octokit.Octokit()

    let contributors = await client.rest.repos.listContributors({owner: 'littlebyteorg', repo: 'appledb'})

    let output = JSON.stringify({"contributors": contributors.data, "apple-data": apple_data_credits})

    let file = await fs.promises.open(credits_file, 'w')

    await file.write(output)
}

module.exports = function register(grunt) {
    grunt.registerTask('credits', 'Update credits data', update_credits)
}