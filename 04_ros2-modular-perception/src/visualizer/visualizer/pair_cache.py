class TimestampPairCache:
    def __init__(self, max_cache_size, timeout_seconds):
        if max_cache_size <= 0:
            raise ValueError('max_cache_size 必须大于 0')

        if timeout_seconds <= 0.0:
            raise ValueError('timeout_seconds 必须大于 0')

        self.max_cache_size = max_cache_size
        self.timeout_seconds = timeout_seconds
        self._images = {}
        self._tracks = {}

    @property
    def size(self):
        return len(self._images) + len(self._tracks)

    def add_image(self, stamp, image, now):
        if stamp in self._tracks:
            tracks, _ = self._tracks.pop(stamp)

            return (
                {
                    'stamp': stamp,
                    'image': image,
                    'tracks': tracks,
                },
                [],
            )

        self._images[stamp] = (image, now)

        return None, self._drop_overflow()

    def add_tracks(self, stamp, tracks, now):
        if stamp in self._images:
            image, _ = self._images.pop(stamp)

            return (
                {
                    'stamp': stamp,
                    'image': image,
                    'tracks': tracks,
                },
                [],
            )

        self._tracks[stamp] = (tracks, now)

        return None, self._drop_overflow()

    def expire(self, now):
        expired = []

        for kind, messages in (
            ('image', self._images),
            ('tracks', self._tracks),
        ):
            for stamp, (_, stored_at) in list(messages.items()):
                if now - stored_at > self.timeout_seconds:
                    del messages[stamp]
                    expired.append((kind, stamp))

        return expired

    def _drop_overflow(self):
        dropped = []

        while self.size > self.max_cache_size:
            oldest = self._oldest_message()

            if oldest is None:
                break

            kind, stamp = oldest

            if kind == 'image':
                del self._images[stamp]
            else:
                del self._tracks[stamp]

            dropped.append((kind, stamp))

        return dropped

    def _oldest_message(self):
        oldest_kind = None
        oldest_stamp = None
        oldest_time = None

        for kind, messages in (
            ('image', self._images),
            ('tracks', self._tracks),
        ):
            for stamp, (_, stored_at) in messages.items():
                if oldest_time is None or stored_at < oldest_time:
                    oldest_kind = kind
                    oldest_stamp = stamp
                    oldest_time = stored_at

        if oldest_kind is None:
            return None

        return oldest_kind, oldest_stamp
