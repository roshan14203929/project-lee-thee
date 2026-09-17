# Global workflow and quality guidelines

## Channels

Confirm the channel at ticket intake and record it with
`kit.py set-platform <project> --platform medichannel|html5` (or pass
`--platform` to `init-project`). MediChannel and HTML5 (M3, CareNet,
ThirdParty) have mutually exclusive coding standards — building under the
wrong ruleset means a complete rebuild — so `new-run` refuses to start until a
platform is set. If a snapshot opens with a "no platform is set" warning, stop
and set the platform before building.

| | MediChannel | HTML5 (M3 / MedPeer / CareNet / ThirdParty) |
|---|---|---|
| Document type | XHTML 1.0 Strict, internal, 960 px | HTML5, external |
| Guideline folder | `guidelines/medichannel/` | `guidelines/m3/` |
| Font-size unit | `px` | `rem` |
| QA workflow | `guidelines/medichannel/qa/` (+ `guidelines/global/qa/`) | `guidelines/global/qa/` only |

- GEN-001 Never cross-apply one channel's `coding/` or `qa/` rules to the other.
