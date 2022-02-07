from aiohttp.web_log import AccessLogger


# extra methods
EXTRA_METHODS = "%s %a %Tf %b %r %{User-Agent}i"


class CustomAccessLogClass(AccessLogger):
    """
    Workaround for logging errors 500 to logger.error instead of logger.info.
    The code below is a light modification of aiohttp.helpers.AccessLogger:
    """
    def __init__(self, logger, log_format=AccessLogger.LOG_FORMAT):
        """Initialise the logger.

        logger is a logger object to be used for logging.
        log_format is an string with apache compatible log format description.

        """
        super().__init__(logger, log_format=log_format)

        _compiled_format = AccessLogger._FORMAT_CACHE.get(EXTRA_METHODS)
        if not _compiled_format:
            _compiled_format = self.compile_format(EXTRA_METHODS)
            AccessLogger._FORMAT_CACHE[EXTRA_METHODS] = _compiled_format

        _, self._extra_methods = _compiled_format

    def _format_line_extra(self, request, response, time):
        return ((key, method(request, response, time))
                for key, method in self._extra_methods)

    def log(self, request, response, time):
        try:
            fmt_info = self._format_line(request, response, time)
            extra_info = self._format_line_extra(request, response, time)

            values = [value for key, value in fmt_info]
            extra = dict()
            for key, value in extra_info:
                if key.__class__ is str:
                    extra[key] = value
                else:
                    if key[0] not in extra:
                        extra[key[0]] = f'{key[1]}: {value}'
                    else:
                        extra[key[0]].append('\n'f'{key[1]}: {value}')

            if response.status // 100 == 5:
                self.logger.error(self._log_format % tuple(values), extra=extra)
            else:
                self.logger.info(self._log_format % tuple(values), extra=extra)
        except Exception:
            self.logger.exception("Error in logging")


