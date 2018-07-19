from flask import request

from jaeger_client import Config
from flask_opentracing import FlaskTracer
from opentracing_instrumentation.client_hooks import install_all_patches
from opentracing_instrumentation.request_context import RequestContextManager


class TracerMiddleware(object):
    def __init__(self, app, name, host='localhost'):
        self.cfg = Config(
            config={
                'sampler': {'type': 'const', 'param': 1},
                'local_agent': {'reporting_host': host}
            },
            service_name=name
        )
        self.app = app
        self.initialized = False

        app.before_request(self._start_trace)
        app.after_request(self._end_trace)

        install_all_patches()

    def _start_trace(self):
        if not self.initialized:
            self.tracer = self.cfg.initialize_tracer()
            self.ftracer = FlaskTracer(self.tracer, False, self.app)
            self.initialized = True
        span = self.ftracer.get_span(request)
        if span is None:
            span = self.tracer.start_span(request.endpoint)
        mgr = RequestContextManager(span=span)
        mgr.__enter__()

        request.span = span
        request.mgr = mgr

    def _end_trace(self, response):
        request.span.finish()
        request.mgr.__exit__()
        return response
