#!/usr/bin/env python

from os.path import join, dirname

from cloudify import ctx

ctx.download_resource(
        join('components', 'utils.py'),
        join(dirname(__file__), 'utils.py'))
import utils  # NOQA

STAGE_SERVICE_NAME = 'stage'

ignore_ui = ctx.instance.runtime_properties['ignore_ui']
print "ignore_ui={0}".format(ignore_ui)
if ignore_ui != 'True':
    ctx.logger.info('Stopping Stage (UI) Service...')
    utils.systemd.stop(STAGE_SERVICE_NAME)
