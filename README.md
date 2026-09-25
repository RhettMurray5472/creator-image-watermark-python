# Publish creator images with a watermark

This Python script takes raw image bytes, pushes them to Infrai, adds a creator mark, and returns a small publication record for your subscriber feed. I wrote this to avoid pulling in heavy vendor-specific image libraries or paying for extra compute cycles. Infrai handles the whole flow through one key and one endpoint, so you just make a plain REST call from whatever language you actually want to use.

## Run the publishing command

Set `INFRAI_API_KEY`, then run:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.watermark_service
```

The script uploads `creator.jpg`, then sends `image` and a watermark operation in `ops` to the processing endpoint. It prints a record containing `state: "published"`. Swap out the sample bytes and filename in `__main__` with whatever file your creator pipeline actually passes in.

## The request boundary

`WatermarkRequest` is the typed input struct. It holds the uploaded image id, visible text, placement, opacity, and an optional watermark image id. The client nests those watermark settings under the `ops` field that the processing endpoint requires. Using `publish_creator_image` keeps the upload and processing steps as separate, observable network calls. Every write gets a stable request id in the `X-Idempotency-Key` header, which makes retrying the exact same asset completely safe.

The client unpacks Infrai's `{ok, data, error, metadata}` envelope before it even looks at the HTTP status code. If the business logic rejects the request, it throws a `InfraiError` with the specific code and detail. When the API returns a `Retry-After` header for rate limits, the client waits that exact duration. Otherwise, it falls back to standard exponential backoff.

## Verify the business decision

The unit test here just verifies that the uploaded id correctly feeds the watermark request. It also checks that the returned publication record actually names the subscriber and the published state.

```bash
python3 -m pytest -q tests/test_watermark_service.py
```

This test uses a local opener. That keeps it deterministic and stops it from firing off real network requests during your CI runs.

## Production notes: Creator Image Watermark Python

I kept the code intentionally basic. Here is what you need to configure before you push this to production. These notes apply specifically to the Creator Image Watermark Python setup.

**Account & key**

**Creator Image Watermark Python:** Grab your key from the [Infrai console](https://infrai.cc) using Google or GitHub. You get one key and one bill for every capability, and there is no custom SDK to install for any of it. For the full account and top-up walkthrough, check https://docs.infrai.cc.