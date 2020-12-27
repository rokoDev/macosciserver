#!/usr/bin/env python3

import requests
import os
import subprocess
import argparse
import sys
from configure_build_test import cmake_configure_build_test

def run(*args):
  command = ['git'] + list(args)
  try:
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    return result.stdout
  except subprocess.CalledProcessError as e:
    s = " "
    print(f"Command [{s.join(command)}] exit with code {e.returncode}")
    print(f"Command output: {e.output}")
    print(f"Command stderr: {e.stderr}")
    sys.exit(e.returncode)

def get_current_branch_name():
  return run("rev-parse", "--abbrev-ref", "HEAD").rstrip('\r\n')

def get_current_commit_sha():
  return run("rev-parse", "HEAD").rstrip('\r\n')

def submodule_update_init_recursive():
  return run("submodule", "update", "--init", "--recursive")

# we assume that every submodule tracking "master" branch.
# If that is not true additional workaround needed to determine submodule branch name.
def checkout_all_submodules():
  run("submodule", "foreach", "--recursive", "git", "checkout", "master")

def update_all_submodules():
  checkout_all_submodules()
  submodule_update_init_recursive()

def switch_to_branch(branch_name):
  CURRENT_BRANCH = get_current_branch_name()
  if CURRENT_BRANCH == branch_name:
    print(f"we are already on source branch <{branch_name}>")
  else:
    print(f"switch branch from <{CURRENT_BRANCH}> to <{branch_name}>")
    run("checkout", "--recurse-submodules", branch_name)
  run("pull")
  update_all_submodules()

def create_and_checkout_branch(branch_name):
  print(f"create and checkout branch <{branch_name}>")
  run("checkout", "-b", branch_name)

def merge_branch_to_current(branch_name):
  CURRENT_BRANCH = get_current_branch_name()
  print(f"merge <{branch_name}> to <{CURRENT_BRANCH}>")
  run("merge", branch_name)

def clone_repo(clone_url):
  print(f"clone from:<{clone_url}>")
  run("clone", clone_url)

def clone_branch(clone_url, branch_name):
  print(f"clone branch <{branch_name}> from <{clone_url}>")
  run("clone", "-b", branch_name, "--single-branch", clone_url)

def checkout_commit(commit_sha):
  print(f"checkout commit:<{commit_sha}>")
  cur_commit_sha = get_current_commit_sha()
  print(f"current commit:<{cur_commit_sha}>")
  if cur_commit_sha != commit_sha:
    run("checkout", commit_sha)
    update_all_submodules()

def main():
  parser = argparse.ArgumentParser(description="""
  This script does:
    1. Figure out source and destination branch names.
    2. Create new branch from destination branch.
    3. Merge source branch to destination branch.
  """)
  parser.add_argument("-BRANCH_NAME", help="Pull request source branch name.")
  parser.add_argument("-COMMIT_SHA", help="Commit SHA which should be treated as HEAD of source branch.")
  parser.add_argument("-CLONE_URL", help="URL which can be used in command:$ git clone URL")
  parser.add_argument("-OWNER_NAME", help="Repository owner name.")
  parser.add_argument("-REPO_NAME", help="Repository name.")
  parser.add_argument("-CI_WORK_PATH", default=os.getenv('./'), help="CI working directory.")

  args = parser.parse_args()
  
  # get source and destination branch names
  BRANCH_NAME = args.BRANCH_NAME
  COMMIT_SHA = args.COMMIT_SHA

  CLONE_URL = args.CLONE_URL
  REPO_NAME = args.REPO_NAME
  OWNER_NAME = args.OWNER_NAME
  CI_WORK_PATH = args.CI_WORK_PATH

  print(f"push on branch:<{BRANCH_NAME}> with commit sha:<{COMMIT_SHA}>")
  print(f"CLONE_URL:<{CLONE_URL}>")
  print(f"REPO_NAME:<{REPO_NAME}>")
  print(f"OWNER_NAME:<{OWNER_NAME}>")
  print(f"CI_WORK_PATH:<{CI_WORK_PATH}>")

  path = os.path.join(CI_WORK_PATH, OWNER_NAME, REPO_NAME, BRANCH_NAME)
  print(f"path:<{path}>")
  os.makedirs(path, exist_ok=True)
  
  os.chdir(path)
  PROJECT_ROOT_PATH = os.path.join(path, REPO_NAME)
  if not os.path.isdir(PROJECT_ROOT_PATH):
    clone_branch(CLONE_URL, BRANCH_NAME)

  os.chdir(PROJECT_ROOT_PATH)
  switch_to_branch(BRANCH_NAME)
  checkout_commit(COMMIT_SHA)

  BUILD_DIR = os.path.join(PROJECT_ROOT_PATH, 'build', 'Xcode')
  NOT_CLEAR_BUILD_DIR = False

  cmake_configure_build_test(False, NOT_CLEAR_BUILD_DIR, 'Debug', 'Xcode', BUILD_DIR, PROJECT_ROOT_PATH)
  cmake_configure_build_test(False, True, 'Release', 'Xcode', BUILD_DIR, PROJECT_ROOT_PATH)

  BUILD_DIR = os.path.join(PROJECT_ROOT_PATH, 'build', 'Ninja', 'Debug')
  cmake_configure_build_test(False, NOT_CLEAR_BUILD_DIR, 'Debug', 'Ninja', BUILD_DIR, PROJECT_ROOT_PATH)

  BUILD_DIR = os.path.join(PROJECT_ROOT_PATH, 'build', 'Ninja', 'Release')
  cmake_configure_build_test(False, NOT_CLEAR_BUILD_DIR, 'Release', 'Ninja', BUILD_DIR, PROJECT_ROOT_PATH)
  sys.exit(0)

if __name__ == "__main__":
  main()
