from visualizer.pair_cache import TimestampPairCache


def test_same_timestamp_forms_a_pair():
    cache = TimestampPairCache(
        max_cache_size=4,
        timeout_seconds=2.0,
    )

    pair, dropped = cache.add_image(
        stamp=(1, 100),
        image='image-message',
        now=0.0,
    )

    assert pair is None
    assert dropped == []

    pair, dropped = cache.add_tracks(
        stamp=(1, 100),
        tracks='tracks-message',
        now=0.1,
    )

    assert dropped == []
    assert pair == {
        'stamp': (1, 100),
        'image': 'image-message',
        'tracks': 'tracks-message',
    }
    assert cache.size == 0


def test_different_timestamps_do_not_pair():
    cache = TimestampPairCache(
        max_cache_size=4,
        timeout_seconds=2.0,
    )

    cache.add_image(
        stamp=(1, 100),
        image='image-message',
        now=0.0,
    )
    pair, dropped = cache.add_tracks(
        stamp=(1, 200),
        tracks='tracks-message',
        now=0.1,
    )

    assert pair is None
    assert dropped == []
    assert cache.size == 2


def test_expired_message_is_removed():
    cache = TimestampPairCache(
        max_cache_size=4,
        timeout_seconds=2.0,
    )

    cache.add_image(
        stamp=(1, 100),
        image='image-message',
        now=0.0,
    )

    expired = cache.expire(now=2.1)

    assert expired == [('image', (1, 100))]
    assert cache.size == 0


def test_oldest_message_is_dropped_when_cache_is_full():
    cache = TimestampPairCache(
        max_cache_size=2,
        timeout_seconds=2.0,
    )

    cache.add_image(
        stamp=(1, 100),
        image='old-image',
        now=0.0,
    )
    cache.add_image(
        stamp=(1, 200),
        image='new-image',
        now=0.1,
    )
    _, dropped = cache.add_tracks(
        stamp=(1, 300),
        tracks='tracks-message',
        now=0.2,
    )

    assert dropped == [('image', (1, 100))]
    assert cache.size == 2
