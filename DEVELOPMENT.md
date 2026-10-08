# Development handoff

## Functionally tested

- Updated browser layout launches successfully.
- Sleeping tabs wake when selected.
- Audio continues while switching tabs in the reported test.
- Manually protected tabs stay awake.
- Disabling Gaming mode wakes sleeping tabs.

## Needs verification

- Persistent website login after a normal quit and restart.
- Background video/call protection across more websites.
- Resource savings under repeatable workloads.

## Performance findings

YouTube test: 1280x720 at 24 fps, AV1 video and Opus audio.
Reported dropped frames: 0 of 4399.

Sequential YouTube runs:
- Gaming off: mean CPU 55.13% of one core, mean PSS 2007.5 MiB.
- Gaming on: mean CPU 60.79% of one core, mean PSS 2005.9 MiB.

These runs did not demonstrate savings and were not controlled enough
to attribute the difference to Gaming mode.

## Video acceleration investigation

GPU: NVIDIA RTX 3060 Ti.
Driver: 595.104.02.
NVIDIA DRM modesetting: enabled.

Installed diagnostic packages:
- libva-utils
- libva-nvidia-driver

This command successfully exposed AV1 decoding support:

```bash
LIBVA_DRIVER_NAME=nvidia NVD_BACKEND=direct vainfo
```

However, Qt WebEngine still reported:
- Video Decode: software only; hardware acceleration disabled.
- AcceleratedVideoDecoder in the disabled-features list.
- Active YouTube decoder: Dav1dVideoDecoder.
- kIsPlatformVideoDecoder: false.

Hardware rendering works, but hardware video decoding is not enabled.
The exact engine condition responsible remains unresolved.

Do not disable sandboxing or web security to work around this.

## Next tasks

1. Verify persistent website sessions.
2. Complete settled-playing versus paused measurements.
3. Investigate a supported Qt/NVIDIA video-acceleration path.
4. Add clear-browsing-data controls.
5. Benchmark against Firefox before claiming lower resource use.


## Update notification test

Test the Nimvex menu badge and scheduled updater.
