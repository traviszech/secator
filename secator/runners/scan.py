import logging

from secator.template import TemplateLoader
from secator.config import CONFIG
from secator.runners._base import Runner
from secator.runners.workflow import Workflow
from secator.output_types import Error
from secator.utils import merge_opts

logger = logging.getLogger(__name__)


class Scan(Runner):

	default_exporters = CONFIG.scans.exporters

	@classmethod
	def delay(cls, *args, **kwargs):
		from secator.celery import run_scan
		return run_scan.delay(args=args, kwargs=kwargs)

	def yielder(self):
		"""Run scan.

		Yields:
			secator.output_types.OutputType: Secator output type.
		"""
		scan_opts = self.config.options
		self.print_item = False
		for name, workflow_opts in self.config.workflows.items():
			run_opts = self.run_opts.copy()
			opts = merge_opts(scan_opts, workflow_opts, run_opts)
			workflow = Workflow(
				TemplateLoader(name=f'workflows/{name}'),
				self.inputs,
				results=self.results,
				run_opts=opts,
				hooks=self._hooks,
				context=self.context.copy())
			yield from workflow
			if len(self.errors) > 0:
				self.add_result(Error(message=f'Stopping scan since workflow {name} has errors'))
				return
