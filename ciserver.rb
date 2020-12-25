require 'sinatra'
require 'json'
require 'octokit'
require 'pathname'

class CIServer < Sinatra::Base

  def initialize
  	super
  	privateFile = File.read('./private_config.json')
  	@privateConfig = JSON.parse(privateFile)
  	file = File.read('./config.json')
    @config = JSON.parse(file)
  end

  before do
    @client = Octokit::Client.new(:access_token => @privateConfig['GIT_TOKEN'])
  end

  post '/event_handler' do
    @payload = JSON.parse(params[:payload])

    case request.env['HTTP_X_GITHUB_EVENT']
    when "pull_request"
      if @payload["action"] == "opened" || @payload['action'] == "synchronize"
        process_pull_request(@payload["pull_request"])
      end
    when "push"
      if !@payload["deleted"]
        process_push()
      end
    end
  end

  helpers do
    def process_pull_request(pull_request)
      puts "Processing pull request..."

      toBranch = pull_request['base']['ref']
      if !is_prs_allowed(toBranch)
      	return
      end
      toSHA = pull_request['base']['sha']

      prTitle = pull_request['title']

      fromBranch = pull_request['head']['ref']
      fromSHA = pull_request['head']['sha']

      cloneUrl = @payload["repository"]["clone_url"]
      repoName = @payload["repository"]["name"]
      prNumber = @payload["number"]
      repoOwnerLogin = @payload["repository"]["owner"]["login"]

      ciWorkPath = @privateConfig['CIWorkPath']

      repo_slug = pull_request['head']['repo']['full_name']
      commit_sha = pull_request['head']['sha']
      
      send_status(repo_slug, commit_sha, 'pending')
      result = system("python3 ./checkout_pr.py -PR_TITLE #{prTitle} -FROM_BRANCH #{fromBranch} -FROM_SHA #{fromSHA} -TO_BRANCH #{toBranch} -TO_SHA #{toSHA} -CLONE_URL #{cloneUrl} -OWNER_NAME #{repoOwnerLogin} -REPO_NAME #{repoName} -PR_NUMBER #{prNumber} -CI_WORK_PATH #{ciWorkPath}")
      if result
        send_status(repo_slug, commit_sha, 'success')
      else
      	send_status(repo_slug, commit_sha, 'failure')
      end
      puts "Pull request processed!"
    end

    def process_push()
      puts "Processing push..."

      branchName = Pathname.new(@payload['ref']).basename

      if !is_pushes_allowed(branchName)
      	return
      end

      commitMsg = @payload["head_commit"]["message"]
      puts "Commit message:<#{commitMsg}>"

      commitSHA = @payload['after']

      cloneUrl = @payload["repository"]["clone_url"]
      repoName = @payload["repository"]["name"]
      repoOwnerLogin = @payload["repository"]["owner"]["login"]

      ciWorkPath = @privateConfig['CIWorkPath']

      repo_slug = @payload['repository']['full_name']

      send_status(repo_slug, commitSHA, 'pending')
      puts "pending status sent!"
      result = system("python3 ./checkout_branch.py -BRANCH_NAME #{branchName} -COMMIT_SHA #{commitSHA} -CLONE_URL #{cloneUrl} -OWNER_NAME #{repoOwnerLogin} -REPO_NAME #{repoName} -CI_WORK_PATH #{ciWorkPath}")
      if result
      	send_status(repo_slug, commitSHA, 'success')
      else
      	send_status(repo_slug, commitSHA, 'failure')
      end
      puts "Push processed!"
    end

    def send_status(repo_slug, commit_sha, status_to_send)
    	puts "<#{status_to_send}> going to be sent!!"
    	@client.create_status(repo_slug, commit_sha, status_to_send)
    end

    def is_prs_allowed(branch_name)
    	branchConfig = @config['branches'].find {|u| u['name'] == branch_name}
        if branchConfig && branchConfig['prs']
          return true
        end
        puts "Processing pull requests for branch <#{branch_name}> isn't configurated"
        return false
    end

    def is_pushes_allowed(branch_name)
    	branchConfig = @config['branches'].find {|u| u['name'] == branch_name}

        if branchConfig && branchConfig['pushes']
          return true
        end
        puts "Processing pushes for branch <#{branch_name}> isn't configurated"
        return false
    end
  end
end
