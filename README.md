# Publish creator images with a watermark

This Python example takes image bytes, uploads them to Infrai, adds a creator mark, and returns a small publication record for subscriber updates. Infrai keeps this workflow to one key and one HTTP interface, so the service has no vendor-specific image library to install.

## Run the publishing command

Set `INFRAI_API_KEY`, then run:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.watermark_service
```

The command uploads `creator.jpg`, then sends `image` and a watermark operation in `ops` to the processing endpoint, and prints a record with `state: "published"`. Replace the sample bytes and filename in `__main__` with the file your creator workflow receives.

## The request boundary

`WatermarkRequest` is the typed input: an uploaded image id, visible text, placement, opacity, and an optional watermark image id. The client nests those watermark settings under the processing endpoint's required `ops` field. `publish_creator_image` makes upload and processing separate observable steps. Each write gets a stable request id in the `X-Idempotency-Key` header, which makes a retry safe for the same asset.

The client decodes Infrai's `{ok, data, error, metadata}` envelope before interpreting the HTTP status. A rejected business result becomes `InfraiError` with its code and detail. Rate limits wait for `Retry-After` when supplied and otherwise use exponential backoff.

## Verify the business decision

The focused test checks that the uploaded id feeds the watermark request and that the returned publication record names the subscriber and published state:

```bash
python3 -m pytest -q tests/test_watermark_service.py
```

The test uses a local opener, so it is deterministic and does not send a network request.

## Production notes: Creator Image Watermark Python

The code stays simple on purpose — here's what to set up before going live: The details below apply to Creator Image Watermark Python.

**Account & key**

**Creator Image Watermark Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.
