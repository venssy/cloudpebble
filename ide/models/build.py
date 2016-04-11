import uuid
import json
from django.conf import settings
from django.db import models
from ide.models.project import Project
from django.utils.translation import ugettext as _

from ide.models.meta import IdeModel

import utils.s3 as s3
__author__ = 'katharine'


class BuildResult(IdeModel):

    STATE_WAITING = 1
    STATE_FAILED = 2
    STATE_SUCCEEDED = 3
    STATE_CHOICES = (
        (STATE_WAITING, _('Pending')),
        (STATE_FAILED, _('Failed')),
        (STATE_SUCCEEDED, _('Succeeded'))
    )

    DEBUG_INFO_MAP = {
        'aplite': ('debug_info.json', 'worker_debug_info.json'),
        'basalt': ('basalt_debug_info.json', 'basalt_worker_debug_info.json'),
        'chalk': ('chalk_debug_info.json', 'chalk_worker_debug_info.json'),
    }
    DEBUG_APP = 0
    DEBUG_WORKER = 1

    project = models.ForeignKey(Project, related_name='builds')
    uuid = models.CharField(max_length=36, default=lambda:str(uuid.uuid4()))
    state = models.IntegerField(choices=STATE_CHOICES, default=STATE_WAITING)
    started = models.DateTimeField(auto_now_add=True, db_index=True)
    finished = models.DateTimeField(blank=True, null=True)

    def _get_dir(self):
        return '%s/' % self.uuid

    def get_url(self):
        return "%s%s/" % (settings.MEDIA_URL, self.uuid)

    def get_pbw_filename(self):
        return '%swatchface.pbw' % self._get_dir()

    def get_build_log(self):
        return '%sbuild_log.txt' % self._get_dir()

    def get_pbw_url(self):
        return '%swatchface.pbw' % self.get_url()

    def get_build_log_url(self):
        return '%sbuild_log.txt' % self.get_url()

    def get_debug_info_filename(self, platform, kind):
        return self._get_dir() + self.DEBUG_INFO_MAP[platform][kind]

    def get_debug_info_url(self, platform, kind):
        return self.get_url() + self.DEBUG_INFO_MAP[platform][kind]

    def get_simplyjs(self):
        return '%ssimply.js' % self._get_dir()

    def get_simplyjs_url(self):
        return '%ssimply.js' % self.get_url()

    def save_build_log(self, text):
        s3.save_file('builds', self.build_log, text, public=True, content_type='text/plain')

    def read_build_log(self):
        return s3.read_file('builds', self.build_log)

    def save_debug_info(self, json_info, platform, kind):
        text = json.dumps(json_info)
        s3.save_file('builds', self.get_debug_info_filename(platform, kind), text, public=True, content_type='application/json')

    def save_pbw(self, pbw_path):
        s3.upload_file('builds', self.pbw, pbw_path, public=True, download_filename='%s.pbw' % self.project.app_short_name.replace('/','-'))

    def save_simplyjs(self, javascript):
        s3.save_file('builds', self.simplyjs, javascript, public=True, content_type='text/javascript')

    pbw = property(get_pbw_filename)
    build_log = property(get_build_log)

    pbw_url = property(get_pbw_url)
    build_log_url = property(get_build_log_url)

    simplyjs = property(get_simplyjs)
    simplyjs_url = property(get_simplyjs_url)

    def get_sizes(self):
        sizes = {}
        for size in self.sizes.all():
            sizes[size.platform] = {
                'total': size.total_size,
                'app': size.binary_size,
                'resources': size.resource_size,
                'worker': size.worker_size,
            }
        return sizes


class BuildSize(IdeModel):
    build = models.ForeignKey(BuildResult, related_name='sizes')

    platform = models.CharField(max_length=20)

    total_size = models.IntegerField(blank=True, null=True)
    binary_size = models.IntegerField(blank=True, null=True)
    resource_size = models.IntegerField(blank=True, null=True)
    worker_size = models.IntegerField(blank=True, null=True)
