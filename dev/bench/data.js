window.BENCHMARK_DATA = {
  "lastUpdate": 1790616741678,
  "repoUrl": "https://github.com/anpawo/Video-Code",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "email": "hippolytelefer@gmail.com",
            "name": "Hip-po",
            "username": "Hip-po"
          },
          "committer": {
            "email": "hippolytelefer@gmail.com",
            "name": "Hip-po",
            "username": "Hip-po"
          },
          "distinct": false,
          "id": "d45262a6932075a1842b3420bb6bfba78e83431e",
          "message": "fix: update regex for whitespace trimming and ensure compatibility with Qt's engine",
          "timestamp": "2026-09-28T00:28:10+02:00",
          "tree_id": "2046aaa84c1f63079b84ea88bd8f692df5cee29e",
          "url": "https://github.com/anpawo/Video-Code/commit/d45262a6932075a1842b3420bb6bfba78e83431e"
        },
        "date": 1790552940652,
        "tool": "customSmallerIsBetter",
        "benches": [
          {
            "name": "bake/applyCalls",
            "value": 21767,
            "unit": "count"
          },
          {
            "name": "bake/entries",
            "value": 18980,
            "unit": "count"
          },
          {
            "name": "bake/inputs",
            "value": 564,
            "unit": "count"
          },
          {
            "name": "render/msPerFrame",
            "value": 6.5429,
            "unit": "ms"
          },
          {
            "name": "render/total",
            "value": 2.4732,
            "unit": "s"
          },
          {
            "name": "render/load",
            "value": 0.5103,
            "unit": "s"
          },
          {
            "name": "render/peakRss",
            "value": 461.2031,
            "unit": "MB"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "rousset.marius13@gmail.com",
            "name": "marius rousset",
            "username": "anpawo"
          },
          "committer": {
            "email": "rousset.marius13@gmail.com",
            "name": "marius rousset",
            "username": "anpawo"
          },
          "distinct": true,
          "id": "a3cb0394c1361c68f174ad18b09a8ed074b5dec3",
          "message": "gitignore: a video's footage stays out of the repository\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-09-28T11:59:18+02:00",
          "tree_id": "238ddff272721563984f53273c0dddb00d64169e",
          "url": "https://github.com/anpawo/Video-Code/commit/a3cb0394c1361c68f174ad18b09a8ed074b5dec3"
        },
        "date": 1790589647841,
        "tool": "customSmallerIsBetter",
        "benches": [
          {
            "name": "bake/applyCalls",
            "value": 21767,
            "unit": "count"
          },
          {
            "name": "bake/entries",
            "value": 18980,
            "unit": "count"
          },
          {
            "name": "bake/inputs",
            "value": 564,
            "unit": "count"
          },
          {
            "name": "render/msPerFrame",
            "value": 6.5429,
            "unit": "ms"
          },
          {
            "name": "render/total",
            "value": 2.4732,
            "unit": "s"
          },
          {
            "name": "render/load",
            "value": 0.5103,
            "unit": "s"
          },
          {
            "name": "render/peakRss",
            "value": 461.2031,
            "unit": "MB"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "rousset.marius13@gmail.com",
            "name": "marius rousset",
            "username": "anpawo"
          },
          "committer": {
            "email": "rousset.marius13@gmail.com",
            "name": "marius rousset",
            "username": "anpawo"
          },
          "distinct": true,
          "id": "ff23a73ef254efb9d8e9bf8dd3bdc35005ac66f6",
          "message": "board: rows keep their GitHub issue in step, landed rows leave\n\ndocs/board_issues.py gives a new row its issue and closes the issue of a row\nwhose fix is on main or that moved to Won't do. The LoL template, the ⌘1..4\nmenus and the timeline span landed; the black preview after a layout switch\njoins To do.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-09-28T12:01:12+02:00",
          "tree_id": "f557b6e4e35a385ac89897a200605d71f5bb1664",
          "url": "https://github.com/anpawo/Video-Code/commit/ff23a73ef254efb9d8e9bf8dd3bdc35005ac66f6"
        },
        "date": 1790590049200,
        "tool": "customSmallerIsBetter",
        "benches": [
          {
            "name": "bake/applyCalls",
            "value": 21767,
            "unit": "count"
          },
          {
            "name": "bake/entries",
            "value": 18980,
            "unit": "count"
          },
          {
            "name": "bake/inputs",
            "value": 564,
            "unit": "count"
          },
          {
            "name": "render/msPerFrame",
            "value": 6.5429,
            "unit": "ms"
          },
          {
            "name": "render/total",
            "value": 2.4732,
            "unit": "s"
          },
          {
            "name": "render/load",
            "value": 0.5103,
            "unit": "s"
          },
          {
            "name": "render/peakRss",
            "value": 461.2031,
            "unit": "MB"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "rousset.marius13@gmail.com",
            "name": "marius rousset",
            "username": "anpawo"
          },
          "committer": {
            "email": "rousset.marius13@gmail.com",
            "name": "marius rousset",
            "username": "anpawo"
          },
          "distinct": true,
          "id": "bc4e93bf673f6c1bc58c201745d728295317b173",
          "message": "preview: a layout switch no longer blacks out the clips\n\nA new pane size rebuilds the preview renderer, and every clip's texture lived\nin the one thrown away — only inputs rebuilt by the last run were uploaded\nagain, so the pane went flat until the scene ran again. A splitter drag did\nthe same. Every Image and Video is now queued again for the new renderer.\n\ntest/editor_preview_resize_test.py takes a frame, presses ⌘4, takes another:\nflat without this, the clip with it.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-09-28T12:18:08+02:00",
          "tree_id": "abadc08b82beff6c616cae028ffc0435c37d55fd",
          "url": "https://github.com/anpawo/Video-Code/commit/bc4e93bf673f6c1bc58c201745d728295317b173"
        },
        "date": 1790590794314,
        "tool": "customSmallerIsBetter",
        "benches": [
          {
            "name": "bake/applyCalls",
            "value": 21767,
            "unit": "count"
          },
          {
            "name": "bake/entries",
            "value": 18980,
            "unit": "count"
          },
          {
            "name": "bake/inputs",
            "value": 564,
            "unit": "count"
          },
          {
            "name": "render/msPerFrame",
            "value": 6.5429,
            "unit": "ms"
          },
          {
            "name": "render/total",
            "value": 2.4732,
            "unit": "s"
          },
          {
            "name": "render/load",
            "value": 0.5103,
            "unit": "s"
          },
          {
            "name": "render/peakRss",
            "value": 461.2031,
            "unit": "MB"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "rousset.marius13@gmail.com",
            "name": "marius rousset",
            "username": "anpawo"
          },
          "committer": {
            "email": "rousset.marius13@gmail.com",
            "name": "marius rousset",
            "username": "anpawo"
          },
          "distinct": true,
          "id": "9e4429615fbf1e416a4e376484fa70009a958f48",
          "message": "board: the black preview after a layout switch landed (bc4e93b)\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-09-28T12:18:34+02:00",
          "tree_id": "e7e605c28eb867d15e8686e1a1da2b2221c42fc7",
          "url": "https://github.com/anpawo/Video-Code/commit/9e4429615fbf1e416a4e376484fa70009a958f48"
        },
        "date": 1790591191437,
        "tool": "customSmallerIsBetter",
        "benches": [
          {
            "name": "bake/applyCalls",
            "value": 21767,
            "unit": "count"
          },
          {
            "name": "bake/entries",
            "value": 18980,
            "unit": "count"
          },
          {
            "name": "bake/inputs",
            "value": 564,
            "unit": "count"
          },
          {
            "name": "render/msPerFrame",
            "value": 6.5429,
            "unit": "ms"
          },
          {
            "name": "render/total",
            "value": 2.4732,
            "unit": "s"
          },
          {
            "name": "render/load",
            "value": 0.5103,
            "unit": "s"
          },
          {
            "name": "render/peakRss",
            "value": 461.2031,
            "unit": "MB"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "rousset.marius13@gmail.com",
            "name": "marius rousset",
            "username": "anpawo"
          },
          "committer": {
            "email": "rousset.marius13@gmail.com",
            "name": "marius rousset",
            "username": "anpawo"
          },
          "distinct": true,
          "id": "ced60e7f4e361c36e62502d77fa69fae6a3c466d",
          "message": "board: the renderer crash, frame hold, LoL hook and agent's changed lines landed\n\nThe crash (#77) leaves the board; the three features stay under Needs your\ncheck with their commits, for an eye or a mouse. fadeIn's hidden and\nwaitFor(clip.end) were on main and asked only a go: they leave too. The\nREADME gif joins the checks.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-09-28T18:13:32+02:00",
          "tree_id": "6456b3c351b9d79226e9cf479a2a69bc0b92d189",
          "url": "https://github.com/anpawo/Video-Code/commit/ced60e7f4e361c36e62502d77fa69fae6a3c466d"
        },
        "date": 1790612137627,
        "tool": "customSmallerIsBetter",
        "benches": [
          {
            "name": "bake/applyCalls",
            "value": 21767,
            "unit": "count"
          },
          {
            "name": "bake/entries",
            "value": 18980,
            "unit": "count"
          },
          {
            "name": "bake/inputs",
            "value": 564,
            "unit": "count"
          },
          {
            "name": "render/msPerFrame",
            "value": 6.5429,
            "unit": "ms"
          },
          {
            "name": "render/total",
            "value": 2.4732,
            "unit": "s"
          },
          {
            "name": "render/load",
            "value": 0.5103,
            "unit": "s"
          },
          {
            "name": "render/peakRss",
            "value": 461.2031,
            "unit": "MB"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "rousset.marius13@gmail.com",
            "name": "marius rousset",
            "username": "anpawo"
          },
          "committer": {
            "email": "rousset.marius13@gmail.com",
            "name": "marius rousset",
            "username": "anpawo"
          },
          "distinct": true,
          "id": "d5e4d8f1f60e11579f66bc9218b40b87124872f2",
          "message": "board: --lint in progress; our own viewer noted as a to-do (79)\n\nPreview does not play a GIF, which is how the idea came up. What only a\nviewer of ours would do — a render next to its golden, the scene lines behind\nthe frame, delivery checks — is in FEATURES_TODO I. Not urgent.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-09-28T18:42:26+02:00",
          "tree_id": "d78d521162121fa1777000ba1d2e39a1fc994e8b",
          "url": "https://github.com/anpawo/Video-Code/commit/d5e4d8f1f60e11579f66bc9218b40b87124872f2"
        },
        "date": 1790613877343,
        "tool": "customSmallerIsBetter",
        "benches": [
          {
            "name": "bake/applyCalls",
            "value": 21767,
            "unit": "count"
          },
          {
            "name": "bake/entries",
            "value": 18980,
            "unit": "count"
          },
          {
            "name": "bake/inputs",
            "value": 564,
            "unit": "count"
          },
          {
            "name": "render/msPerFrame",
            "value": 6.5429,
            "unit": "ms"
          },
          {
            "name": "render/total",
            "value": 2.4732,
            "unit": "s"
          },
          {
            "name": "render/load",
            "value": 0.5103,
            "unit": "s"
          },
          {
            "name": "render/peakRss",
            "value": 461.2031,
            "unit": "MB"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "rousset.marius13@gmail.com",
            "name": "marius rousset",
            "username": "anpawo"
          },
          "committer": {
            "email": "rousset.marius13@gmail.com",
            "name": "marius rousset",
            "username": "anpawo"
          },
          "distinct": true,
          "id": "43266ed37cb87042811bfacb40727b8c482fb5d1",
          "message": "Revert \"probe: a click moves on the spot between press and release\"\n\nThis reverts commit 181eaad. On the Linux runner it fixed neither of\ntimeline_drag's two Click: checks and broke four more: CI went from 2 failures\n(run 36408958368) to 6 (run 36449531410) — the release now writes an edit, so\nthe move turns the click into a drag there. The commit's claim that the clicks\npass came from a debug run, not the full suite. Row 68 stays in progress.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-09-28T18:44:27+02:00",
          "tree_id": "dfac083e091f11b9c95977202bc08046a28be821",
          "url": "https://github.com/anpawo/Video-Code/commit/43266ed37cb87042811bfacb40727b8c482fb5d1"
        },
        "date": 1790614433340,
        "tool": "customSmallerIsBetter",
        "benches": [
          {
            "name": "bake/applyCalls",
            "value": 21767,
            "unit": "count"
          },
          {
            "name": "bake/entries",
            "value": 18980,
            "unit": "count"
          },
          {
            "name": "bake/inputs",
            "value": 564,
            "unit": "count"
          },
          {
            "name": "render/msPerFrame",
            "value": 6.5429,
            "unit": "ms"
          },
          {
            "name": "render/total",
            "value": 2.4732,
            "unit": "s"
          },
          {
            "name": "render/load",
            "value": 0.5103,
            "unit": "s"
          },
          {
            "name": "render/peakRss",
            "value": 461.2031,
            "unit": "MB"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "rousset.marius13@gmail.com",
            "name": "marius rousset",
            "username": "anpawo"
          },
          "committer": {
            "email": "rousset.marius13@gmail.com",
            "name": "marius rousset",
            "username": "anpawo"
          },
          "distinct": true,
          "id": "c63ba697828435e11d2ab4dbf14a9632977b2f28",
          "message": "board: --lint landed, to be seen in the editor; the stale backdated-write warning noted (80)\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-09-28T19:30:37+02:00",
          "tree_id": "e90d8d1a71c780646f9e5397fbfa5af39af2b1ba",
          "url": "https://github.com/anpawo/Video-Code/commit/c63ba697828435e11d2ab4dbf14a9632977b2f28"
        },
        "date": 1790616740870,
        "tool": "customSmallerIsBetter",
        "benches": [
          {
            "name": "bake/applyCalls",
            "value": 21767,
            "unit": "count"
          },
          {
            "name": "bake/entries",
            "value": 18980,
            "unit": "count"
          },
          {
            "name": "bake/inputs",
            "value": 564,
            "unit": "count"
          },
          {
            "name": "render/msPerFrame",
            "value": 6.5429,
            "unit": "ms"
          },
          {
            "name": "render/total",
            "value": 2.4732,
            "unit": "s"
          },
          {
            "name": "render/load",
            "value": 0.5103,
            "unit": "s"
          },
          {
            "name": "render/peakRss",
            "value": 461.2031,
            "unit": "MB"
          }
        ]
      }
    ]
  }
}