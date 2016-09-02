#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © 2016 James R. Barlow: github.com/jbarlow83
# Release sanity checking

import argparse
from subprocess import run, PIPE, DEVNULL, STDOUT, CalledProcessError
from git import Repo, Remote, PushInfo
import logging
import re
import sys
import os


logging.basicConfig(level=logging.INFO)

REMOTE_ERROR_FLAGS = \
    PushInfo.REJECTED | PushInfo.NO_MATCH | PushInfo.REMOTE_REJECTED | \
    PushInfo.REMOTE_FAILURE | PushInfo.DELETED | PushInfo.ERROR


def test_repo(repo):
    assert not repo.is_dirty(), "Repository is dirty"
    if repo.untracked_files:
        logging.warning('Some files are untracked:')
        logging.warning('\n' + '\n'.join(repo.untracked_files))
    assert repo.active_branch.name == 'master', 'Not on branch master'


def travis(args):
    repo = Repo('.')
    test_repo(repo)

    git_describe = repo.git.describe()

    try:
        env = os.environ.copy()
        env['SETUPTOOLS_SCM_PRETEND_VERSION'] = git_describe
        proc = run(['check-manifest'], check=True, universal_newlines=True, stdout=PIPE, stderr=STDOUT, env=env)
        logging.info(proc.stdout)
    except CalledProcessError as e:
        logging.error('MANIFEST.in error')
        logging.error(e.stdout)
        sys.exit(1)

    run(['python3', 'setup.py', 'build'], check=True)

    origin = Remote(repo, 'jbarlow')
    result = origin.push(refspec='master:master')[0]

    if result.flags & REMOTE_ERROR_FLAGS:
        logging.error(result.summary)
        sys.exit(1)
    else:
        logging.info(result.summary)

    logging.info("Pushed to Travis CI")
    logging.info("If this passes, git tag and release")


def release(args):
    repo = Repo('.')
    test_repo(repo)

    git_describe = repo.git.describe()

    assert git_describe.startswith('v') and not '-' in git_describe and not '+ng' in git_describe, \
        "Not tagged properly for release: " + git_describe

    plain_version = git_describe[1:]  # without 'v' prefix

    with open('RELEASE_NOTES.rst') as f:
        notes = f.read()
        assert plain_version in notes, "Version not mentioned in release notes"

    proc = run(['python3', 'setup.py', 'sdist', 'bdist_wheel'], universal_newlines=True, check=True, stdout=PIPE, stderr=STDOUT)
    logging.info(proc.stdout)


    origin = Remote(repo, 'jbarlow')
    result = origin.push(refspec='master:master', tags=True)[0]
    if result.flags & REMOTE_ERROR_FLAGS:
        logging.error(result.summary)
        sys.exit(1)
    else:
        logging.info(result.summary)

    run(['twine', 'upload', '-r', 'pypitest',
        'dist/ocrmypdf-{}.tar.gz'.format(plain_version),
        'dist/ocrmypdf-{}-py34-none-any.whl'.format(plain_version)], check=True, universal_newlines=True, stdout=PIPE)


parser = argparse.ArgumentParser(description="ocrmypdf release tasks")
subparsers = parser.add_subparsers()

push_travis = subparsers.add_parser(
    'push-travis', description="Push master to travis for testing")
push_travis.set_defaults(func=travis)

release_parser = subparsers.add_parser(
    'release', description="Release to PyPI etc")
release_parser.set_defaults(func=release)


def main():
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
