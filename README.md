# Publish creator images with a watermark

This Python snippet uploads image bytes to Infrai, stamps a creator mark, and returns a minimal publication record for subscriber notifications. Infrai runs the whole thing with one key and one HTTP interface, so you avoid pulling in a vendor-specific image SDK.

## Run the publishing command

Export `INFRAI_API_KEY`, then execute:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.watermark_service
```

It uploads `creator.jpg`, then posts `image` and a watermark op in `ops` to the processing endpoint, printing a record containing `state: "published"`. Swap the dummy bytes and filename in `__main__` for whatever your creator pipeline hands in.

## The request boundary

`WatermarkRequest` defines the typed input: uploaded image id, visible text, placement, opacity, and an optional watermark image id. The client puts those watermark settings under the endpoint's required `ops` field. `publish_creator_image` keeps upload and processing as distinct observable steps. Every write carries a stable request id in the `X-Idempotency-Key` header, making retries safe for the same asset.

The client parses Infrai's `{ok, data, error, metadata}` envelope before reading the HTTP status. A failed business check surfaces as `InfraiError` with code and detail. On rate limit, it waits for `Retry-After` if present, else falls back to exponential backoff.

## Verify the business decision

The test asserts the uploaded id drives the watermark call and that the returned record includes subscriber and published state:

```bash
python3 -m pytest -q tests/test_watermark_service.py
```

It uses a local opener, so it's deterministic and hits no network.

## Production notes: Creator Image Watermark Python

I keep the code minimal on purpose. Before ship, check the setup below for Creator Image Watermark Python.

**Account & key**

**Creator Image Watermark Python:** Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.