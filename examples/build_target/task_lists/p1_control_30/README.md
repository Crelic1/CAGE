# P1 AWPB/APB 30-task control subset

This is a static-material observation subset. It makes **no R/X claim** and was selected without running an agent or model.

## Frozen provenance

- Profile rule: `pwn-material-profile-v2`
- Profile plan SHA-256: `6930b606054cc605b461634fd34e11c7e838f5b4227b1c4a4529175715002c8e`
- Profile run: `pwn-material-profile:pwn-material-profile-v2:6930b606054cc605b461634f`
- Entity rule/run: `pwn-material-file-classifier-v11` / `pwn-material-full:pwn-material-file-classifier-v11:ccf9eeb8f6100c25b772`
- Entity selection SHA-256: `ccf9eeb8f6100c25b772faccbb966f366dddf1342863501e54f41388078d3eaa`
- Source repository commit: `74ae7518b477d40a09bfb0ef47e284e785ec707e`
- Catalog schema version: `15`
- Selection seed: `cage-build-target-p1-awpb-apb-30-v1`
- Selection SHA-256: `63c6d973ec8d2453fe14b4ee72c7936370c0a4693f6e4009adeff69816ebfcc3`

Generation command:

```bash
python examples/build_target/scripts/materialize_p1_control_subset.py generate --source-root /mnt/olddata/home/yihe/workspace/ctf-env-collection --dataset /mnt/olddata/home/yihe/workspace/CAGE-bt-r4/.cage/build-target/p1-awpb-apb-30 --manifest /mnt/olddata/home/yihe/workspace/CAGE-bt-r4/examples/build_target/task_lists/p1_control_30/manifest.json --report /mnt/olddata/home/yihe/workspace/CAGE-bt-r4/examples/build_target/task_lists/p1_control_30/README.md --seed cage-build-target-p1-awpb-apb-30-v1
```

## Distribution

- Profiles: `APB` 15, `AWPB` 15
- Unique events: 30
- Unique source repositories: 30
- Years: `2015` 1, `2016` 1, `2017` 1, `2018` 2, `2019` 1, `2020` 1, `2021` 4, `2022` 5, `2023` 4, `2024` 4, `2025` 4, `2026` 2
- Build forms: `build_metadata` 8, `compose` 1, `dockerfile` 10, `dockerfile_compose` 11
- Build modes: `hybrid` 14, `nonstandard` 1, `prebuilt_rehost` 6, `source_build` 9
- Runtime forms: `bundled_libc_loader` 6, `bundled_libc_only` 3, `bundled_loader_only` 1, `musl` 2, `static` 5, `system_libc` 6, `unknown_or_non_elf` 7
- Exploit classes: `format_string` 7, `heap` 9, `kernel` 8, `other` 9, `shellcode_seccomp` 10, `stack_rop` 17, `vm_emulator` 7
- Topology: `multi_service` 3, `single_service` 27
- Complexity: `large` 9, `medium` 11, `small` 10

## Selected tasks

| # | challenge_id | profile / route | source / event / year | build | runtime | exploit | topology | material |
|---:|---|---|---|---|---|---|---|---:|
| 1 | `saj-2024-pwn-no-handouts` | `AWPB` / `fast_track_full` | `cscosu/buckeyectf-2024-public` / BuckeyeCTF / 2024 | `dockerfile_compose`, `hybrid` | `bundled_libc_loader` | heap, shellcode_seccomp, stack_rop | `single_service` | 15 / 6.6 MiB |
| 2 | `gh-bd3f41301aa39ea27de0eeb3` | `APB` / `fast_track_no_writeup` | `Super-Guesser/ctf` / pbctf / 2020 | `dockerfile`, `hybrid` | `bundled_libc_only` | format_string, heap, shellcode_seccomp, stack_rop | `single_service` | 12 / 4.4 MiB |
| 3 | `saj-2026-pwn-67-revenge` | `AWPB` / `fast_track_full` | `0xFunCTF/0xFunCTF-2026-Public` / 0xFUN / 2026 | `dockerfile_compose`, `prebuilt_rehost` | `bundled_libc_loader` | heap, shellcode_seccomp, stack_rop | `single_service` | 12 / 2.3 MiB |
| 4 | `gh-9cfba69f8c90cb227725477e` | `APB` / `fast_track_no_writeup` | `teambi0s/INCTFj_Finals_2024-25` / INCTFj Finals / 2024 | `dockerfile`, `prebuilt_rehost` | `system_libc` | format_string, heap, stack_rop | `single_service` | 4 / 19.3 KiB |
| 5 | `saj-2022-pwn-data-eater` | `AWPB` / `fast_track_full` | `dicegang/dicectf-2022-challenges` / DiceCTF / 2022 | `dockerfile`, `hybrid` | `system_libc` | format_string, stack_rop | `single_service` | 14 / 2.0 MiB |
| 6 | `gh-067edee0402ab57a169029ae` | `APB` / `fast_track_no_writeup` | `dimasma0305/My-CTF-Challenges` / Intechfest / 2023 | `dockerfile_compose`, `hybrid` | `bundled_libc_only` | stack_rop | `multi_service` | 16 / 6.4 MiB |
| 7 | `saj-2021-pwn-kqueue` | `AWPB` / `fast_track_full` | `teambi0s/InCTFi` / InCTF / 2021 | `dockerfile_compose`, `source_build` | `unknown_or_non_elf` | heap, kernel, shellcode_seccomp | `single_service` | 20 / 12.3 MiB |
| 8 | `saj-2025-pwn-cursed-format` | `APB` / `fast_track_no_writeup` | `MasonCompetitiveCyber/PatriotCTF2024` / PatriotCTF / 2025 | `dockerfile`, `source_build` | `bundled_libc_loader` | stack_rop | `single_service` | 16 / 2.0 MiB |
| 9 | `saj-2024-pwn-xss-finder-tool` | `AWPB` / `fast_track_full` | `intigriti/CTF` / 1337UP / 2024 | `dockerfile_compose`, `hybrid` | `static` | shellcode_seccomp, stack_rop, vm_emulator | `multi_service` | 102 / 99.0 MiB |
| 10 | `gh-10b815656e32700eed11ec07` | `APB` / `fast_track_no_writeup` | `ChaO-0/WriteUps` / Arkavidia / 2019 | `dockerfile`, `prebuilt_rehost` | `system_libc` | other | `single_service` | 3 / 9.5 KiB |
| 11 | `gh-4aaa3bc687f9a4ebc31dc755` | `AWPB` / `fast_track_full` | `athack-ctf/AtHackCTF-2025-Challenges` / AtHackCTF / 2025 | `dockerfile_compose`, `source_build` | `bundled_libc_only` | format_string, stack_rop | `single_service` | 8 / 2.0 MiB |
| 12 | `saj-2021-pwn-ebpf` | `APB` / `fast_track_no_writeup` | `sajjadium/ctf-archives` / GoogleCTF / 2021 | `build_metadata`, `source_build` | `musl` | heap, kernel | `single_service` | 13 / 17.6 MiB |
| 13 | `saj-2022-pwn-babyheap2022` | `AWPB` / `fast_track_full` | `0ops/ctfs` / 0CTF / 2022 | `dockerfile_compose`, `prebuilt_rehost` | `system_libc` | heap, shellcode_seccomp, stack_rop | `single_service` | 22 / 434.7 KiB |
| 14 | `gh-c1e81f2d4281418ac05aa50a` | `APB` / `fast_track_no_writeup` | `M0ngi/CTF-Writeups` / Hackfest / 2023 | `dockerfile`, `prebuilt_rehost` | `bundled_libc_loader` | other | `single_service` | 6 / 2.2 MiB |
| 15 | `gh-d9f263b7fbb551151920acd8` | `AWPB` / `fast_track_full` | `sixstars/CTF` / hacklu / 2018 | `build_metadata`, `hybrid` | `static` | kernel | `single_service` | 21 / 100.4 MiB |
| 16 | `saj-2023-pwn-enterprise-blockchain` | `APB` / `fast_track_no_writeup` | `paradigmxyz/paradigm-ctf-2022` / Paradigm / 2023 | `dockerfile_compose`, `source_build` | `unknown_or_non_elf` | other | `multi_service` | 208 / 1.1 MiB |
| 17 | `saj-2022-pwn-krce` | `AWPB` / `fast_track_full` | `zer0pts/zer0pts-CTF-2022-Public` / zer0pts / 2022 | `build_metadata`, `hybrid` | `system_libc` | heap, kernel, stack_rop, vm_emulator | `single_service` | 13 / 7.1 MiB |
| 18 | `saj-2025-pwn-debuggable-3` | `APB` / `fast_track_no_writeup` | `ctf-gg/smileyctf-2025` / smileyCTF / 2025 | `dockerfile`, `source_build` | `unknown_or_non_elf` | format_string, heap, kernel, shellcode_seccomp, stack_rop, vm_emulator | `single_service` | 12 / 849.3 KiB |
| 19 | `gh-c328110b6995cac10415133f` | `AWPB` / `fast_track_full` | `ByteBandits/writeups` / ekoparty pre ctf / 2015 | `build_metadata`, `source_build` | `unknown_or_non_elf` | other | `single_service` | 6 / 5.5 KiB |
| 20 | `gh-0f2902ebb6dd523a62b57f35` | `APB` / `fast_track_no_writeup` | `SECCON/SECCON2017_online_CTF` / SECCON online CTF / 2017 | `build_metadata`, `source_build` | `unknown_or_non_elf` | other | `single_service` | 12 / 42.1 KiB |
| 21 | `gh-782a235ced7e786036e76321` | `AWPB` / `fast_track_full` | `kam1tsur3/2021_CTF` / cakectf / 2021 | `build_metadata`, `hybrid` | `static` | kernel, shellcode_seccomp, vm_emulator | `single_service` | 34 / 29.4 MiB |
| 22 | `gh-5b9c34450c85a9f0fda4a921` | `APB` / `fast_track_no_writeup` | `quanyang/x-ctf-2016-finals` / x ctf / 2016 | `dockerfile`, `hybrid` | `system_libc` | other | `single_service` | 14 / 16.4 KiB |
| 23 | `saj-2023-pwn-full-chain-wall-sina` | `AWPB` / `fast_track_full` | `hitconctf/ctf2023.hitcon.org` / HITCON / 2023 | `dockerfile_compose`, `hybrid` | `bundled_libc_loader` | format_string, shellcode_seccomp, stack_rop, vm_emulator | `single_service` | 21 / 49.5 MiB |
| 24 | `saj-2022-pwn-pointytail` | `APB` / `fast_track_no_writeup` | `Social-Engineering-Experts/SEETF-2022-Public` / SEETF / 2022 | `dockerfile_compose`, `nonstandard` | `unknown_or_non_elf` | other | `single_service` | 5 / 11.1 KiB |
| 25 | `saj-2024-pwn-backup-power` | `AWPB` / `fast_track_full` | `sigpwny/2024-ectf-uiuc` / UIUCTF / 2024 | `dockerfile`, `hybrid` | `static` | format_string, stack_rop, vm_emulator | `single_service` | 19 / 742.0 KiB |
| 26 | `saj-2022-pwn-babyheapng` | `APB` / `fast_track_no_writeup` | `TJCSec/tjctf-2022-challenges` / TJCTF / 2022 | `dockerfile`, `prebuilt_rehost` | `musl` | other | `single_service` | 5 / 22.5 KiB |
| 27 | `gh-7a7e006afd0b331da2a4be1f` | `AWPB` / `fast_track_full` | `0xbada/ctfrepo` / Blaze CTF / 2018 | `build_metadata`, `source_build` | `unknown_or_non_elf` | kernel, shellcode_seccomp, stack_rop | `single_service` | 8 / 64.0 MiB |
| 28 | `gh-4b21898e8a2d18878d06a239` | `APB` / `fast_track_no_writeup` | `Underr00ted/Fennec-CTF-2026-challenges` / Fennec CTF / 2026 | `dockerfile_compose`, `hybrid` | `static` | kernel, stack_rop, vm_emulator | `single_service` | 20 / 66.6 MiB |
| 29 | `gh-8c1099152bc23db3ebb9f4a6` | `AWPB` / `fast_track_full` | `TheDeppSide/my-challs` / m0lecon beginners / 2025 | `compose`, `hybrid` | `bundled_libc_loader` | other | `single_service` | 8 / 2.3 MiB |
| 30 | `gh-46626c6f2dcb825e16557526` | `APB` / `fast_track_no_writeup` | `acdwas/ctf` / 0x41414141 / 2021 | `build_metadata`, `hybrid` | `bundled_loader_only` | stack_rop | `single_service` | 9 / 18.7 MiB |

## Per-task material audit

### 1. `saj-2024-pwn-no-handouts` — no_handouts

- Identity: BuckeyeCTF / 2024 / Pwn
- Source: `cscosu/buckeyectf-2024-public`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/BuckeyeCTF/2024/pwn/no_handouts`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `bundled_libc_loader`; `heap`, `shellcode_seccomp`, `stack_rop`
- Selection reason: fills build_form:dockerfile_compose; fills build_mode:hybrid; fills complexity:medium; fills exploit:heap; fills exploit:shellcode_seccomp; fills exploit:stack_rop; fills runtime:bundled_libc_loader; fills year_bucket:2024; adds event BuckeyeCTF; adds year 2024; adds source cscosu/buckeyectf-2024-public
- Material fingerprint: `5c00c2927f0a22c12c886b1e29708972839f6a508588effe2f979c7bb798e8a3`
- Material paths:
  - A (9):
    - `materials/attachments/chall` ← `work/materials/pwn-v11/saj-2024-pwn-no-handouts/public/chall` (`8751195b7ede31376a0d0be4809dd66941addf1bba861094a4bd2230f3377279`, 16921 bytes)
    - `materials/attachments/chall.c` ← `work/materials/pwn-v11/saj-2024-pwn-no-handouts/public/chall.c` (`1c5dc8d44ccfd7d6e2356c65b54c0e6bbc6886429e7ff4b91232f36832b64009`, 515 bytes)
    - `materials/attachments/challenge.yaml` ← `work/materials/pwn-v11/saj-2024-pwn-no-handouts/public/challenge.yaml` (`ab97cc26a8f51b61ef5a5abef75f86016a9a4d1a71e68d5eb265fc21326d2250`, 577 bytes)
    - `materials/attachments/go.py` ← `work/materials/pwn-v11/saj-2024-pwn-no-handouts/public/go.py` (`271a6393dd3c59ea33341fd2694192c0e1958f9380b65e19494746dc82e034ee`, 1258 bytes)
    - `materials/attachments/handout.py` ← `work/materials/pwn-v11/saj-2024-pwn-no-handouts/public/handout.py` (`472706e5384b3e29a53f138b6e63e6acaaa5c4e315c66627da60a9b851ab9812`, 2229 bytes)
    - `materials/attachments/make_dist.sh` ← `work/materials/pwn-v11/saj-2024-pwn-no-handouts/public/make_dist.sh` (`abdbed45f77a3bfe4323198adc3690c1d4fbb056f90cafed6764833ecd57e214`, 279 bytes)
    - `materials/attachments/program/chall` ← `work/materials/pwn-v11/saj-2024-pwn-no-handouts/public/program/chall` (`095a291642405d4ee5fb52f763d54cfb3e5d04c917b939e3c33f953043b90707`, 16320 bytes)
    - `materials/attachments/program/ld-linux-x86-64.so.2` ← `work/materials/pwn-v11/saj-2024-pwn-no-handouts/public/program/ld-linux-x86-64.so.2` (`595bcdc306999711a5a9c787e5d01618f94eb92c4c09a178e875a324f1072d89`, 240936 bytes)
    - `materials/attachments/program/libc.so.6` ← `work/materials/pwn-v11/saj-2024-pwn-no-handouts/public/program/libc.so.6` (`799afb7e84a4cfe473af8c3cf0c1ff75b6e2d40434f5f00a74c2a3e50625829f`, 6622840 bytes)
  - W (1):
    - `materials/writeups/writeup.md` ← `work/materials/pwn-v11/saj-2024-pwn-no-handouts/writeups/writeup.md` (`ce1e5680d7d42b3e84c9bea729992e4dc0f8da2abce2f9480b159bda6264fafc`, 2390 bytes)
  - P (1):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2024-pwn-no-handouts/solve/solve.py` (`14df76c9cee35b0c122bebc521683d6f6795b266e2bbd011d669ddbe330f9d3e`, 1713 bytes)
  - B (4):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2024-pwn-no-handouts/build/Dockerfile` (`05923e76a23c88d77e15ebd5f04c214e07900d852601e0d63de7eee4dea8e431`, 286 bytes)
    - `materials/deployment/chall.c` ← `work/materials/pwn-v11/saj-2024-pwn-no-handouts/build/chall.c` (`1c5dc8d44ccfd7d6e2356c65b54c0e6bbc6886429e7ff4b91232f36832b64009`, 515 bytes)
    - `materials/deployment/docker-compose.yaml` ← `work/materials/pwn-v11/saj-2024-pwn-no-handouts/build/docker-compose.yaml` (`5f4b51d93688916990db8630d6f4767c6c155d1b1adb2c49927d8fb70a010b26`, 79 bytes)
    - `materials/deployment/make_dist.sh` ← `work/materials/pwn-v11/saj-2024-pwn-no-handouts/build/make_dist.sh` (`abdbed45f77a3bfe4323198adc3690c1d4fbb056f90cafed6764833ecd57e214`, 279 bytes)

### 2. `gh-bd3f41301aa39ea27de0eeb3` — pwnception

- Identity: pbctf / 2020 / Pwn
- Source: `Super-Guesser/ctf`; `https://github.com/Super-Guesser/ctf/tree/21ad5acdc39be59af80cc43412912ec662d0e695/2020/pbctf 2020/pwn/pwnception`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `bundled_libc_only`; `format_string`, `heap`, `shellcode_seccomp`, `stack_rop`
- Selection reason: fills build_form:dockerfile; fills build_mode:hybrid; fills complexity:medium; fills exploit:format_string; fills exploit:heap; fills exploit:shellcode_seccomp; fills exploit:stack_rop; fills runtime:bundled_libc_only; fills year_bucket:2020_2021; adds event pbctf; adds year 2020; adds source Super-Guesser/ctf
- Material fingerprint: `81c0ac43f4b4a9066169eb9837ff64eb85cd03616f6b7aee070eab1f4db97bf4`
- Material paths:
  - A (8):
    - `materials/attachments/dist/challenge/kernel` ← `work/materials/pwn-v11/gh-bd3f41301aa39ea27de0eeb3/public/dist/challenge/kernel` (`ce519f0101e532ad0a7841e88e4870c4ab8112a2349fb7f1d03fc9e368561a3f`, 4888 bytes)
    - `materials/attachments/dist/challenge/libc.so.6` ← `work/materials/pwn-v11/gh-bd3f41301aa39ea27de0eeb3/public/dist/challenge/libc.so.6` (`799a86fec8450776b0b15e40f4e184df609c1ee4bb7f9d0d861cb292a38efd43`, 2030928 bytes)
    - `materials/attachments/dist/challenge/libunicorn.so.1` ← `work/materials/pwn-v11/gh-bd3f41301aa39ea27de0eeb3/public/dist/challenge/libunicorn.so.1` (`43f2606862fbee1cb7128bc674ad794bdfae730fc3cf1f1689b95fc038660891`, 2520984 bytes)
    - `materials/attachments/dist/challenge/main` ← `work/materials/pwn-v11/gh-bd3f41301aa39ea27de0eeb3/public/dist/challenge/main` (`70158693bbf8e7c0ae87b0a14847b70be829eee6e292f09db7599d3ce8babacb`, 18424 bytes)
    - `materials/attachments/dist/challenge/userland` ← `work/materials/pwn-v11/gh-bd3f41301aa39ea27de0eeb3/public/dist/challenge/userland` (`adfce67229cb17edd3b139a0c0bf5e415485496a94f195696afd9c9ddb08e994`, 5136 bytes)
    - `materials/attachments/dist/config/ctf.xinetd` ← `work/materials/pwn-v11/gh-bd3f41301aa39ea27de0eeb3/public/dist/config/ctf.xinetd` (`33fa990de827f916269f821695f020594ba56ae3ada67cc1ec5d15f081acb6d0`, 174 bytes)
    - `materials/attachments/dist/config/run_challenge.sh` ← `work/materials/pwn-v11/gh-bd3f41301aa39ea27de0eeb3/public/dist/config/run_challenge.sh` (`b23d7a3360f50f42501044bfc48789afa16219a18078b7c3a9306cb60dae648c`, 68 bytes)
    - `materials/attachments/sol.py` ← `work/materials/pwn-v11/gh-bd3f41301aa39ea27de0eeb3/public/sol.py` (`d440d7dab41e11f6c9a77806f553e7fe90e2211b3794cc9cc927ea0ce4b6e440`, 1372 bytes)
  - W: absent
  - P (2):
    - `materials/exploit/dist/challenge/solve.py` ← `work/materials/pwn-v11/gh-bd3f41301aa39ea27de0eeb3/solve/dist/challenge/solve.py` (`782fc18ae038571be2d5a6f023389bdabce215b4220024753622e2e61fd77fea`, 7145 bytes)
    - `materials/exploit/exploit.py` ← `work/materials/pwn-v11/gh-bd3f41301aa39ea27de0eeb3/solve/exploit.py` (`ce10f53775fb7569b2b378e27f2ec58dc83d4fda7ef8932e8830c68cfd84f848`, 7760 bytes)
  - B (2):
    - `materials/deployment/dist/Dockerfile` ← `work/materials/pwn-v11/gh-bd3f41301aa39ea27de0eeb3/build/dist/Dockerfile` (`461df4f564a66ffbc483022e96f32c0af80920219cb3447364b5558b19639328`, 873 bytes)
    - `materials/deployment/dist/config/run_challenge.sh` ← `work/materials/pwn-v11/gh-bd3f41301aa39ea27de0eeb3/build/dist/config/run_challenge.sh` (`b23d7a3360f50f42501044bfc48789afa16219a18078b7c3a9306cb60dae648c`, 68 bytes)

### 3. `saj-2026-pwn-67-revenge` — 67_revenge

- Identity: 0xFUN / 2026 / Pwn
- Source: `0xFunCTF/0xFunCTF-2026-Public`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/0xFUN/2026/pwn/67_revenge`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `prebuilt_rehost`; `bundled_libc_loader`; `heap`, `shellcode_seccomp`, `stack_rop`
- Selection reason: fills build_form:dockerfile_compose; fills build_mode:prebuilt_rehost; fills complexity:medium; fills exploit:heap; fills exploit:shellcode_seccomp; fills exploit:stack_rop; fills runtime:bundled_libc_loader; fills year_bucket:2025_plus; adds event 0xFUN; adds year 2026; adds source 0xFunCTF/0xFunCTF-2026-Public
- Material fingerprint: `2acf6fc5817f93640612227882df4456101c41d95a0cd8908df592c3860e330b`
- Material paths:
  - A (7):
    - `materials/attachments/README.md` ← `work/materials/pwn-v11/saj-2026-pwn-67-revenge/public/README.md` (`5e4d906e30fae13446064abbac29105e24030573a522085c20bb373b5250051a`, 38 bytes)
    - `materials/attachments/chall` ← `work/materials/pwn-v11/saj-2026-pwn-67-revenge/public/chall` (`8c5eb40be2c656877034b2cb8ef7ebc886bd1502fd1c0db4b7fb206d4e30c7b8`, 16784 bytes)
    - `materials/attachments/challenge.json` ← `work/materials/pwn-v11/saj-2026-pwn-67-revenge/public/challenge.json` (`501be3775716004ce3f8672268b050366feeec28a358cfd3f8a810e4d532fe2f`, 1505 bytes)
    - `materials/attachments/ld-linux-x86-64.so.2` ← `work/materials/pwn-v11/saj-2026-pwn-67-revenge/public/ld-linux-x86-64.so.2` (`cf4284b901dd56ca86e605d96cb6251d058c8f7a283d6c2a918430041d51a715`, 234400 bytes)
    - `materials/attachments/libc.so.6` ← `work/materials/pwn-v11/saj-2026-pwn-67-revenge/public/libc.so.6` (`b5dfc3e5f5a793055443bd25cb2c7015e4bd9375e2be6b67bf5613e6c20d69b2`, 2010392 bytes)
    - `materials/attachments/libseccomp.so.2` ← `work/materials/pwn-v11/saj-2026-pwn-67-revenge/public/libseccomp.so.2` (`7cb971c30c6e854dedffe8b74f7548ed8f7b0f2e03233cd00f61f76a334dc5c3`, 182288 bytes)
    - `materials/attachments/output.txt` ← `work/materials/pwn-v11/saj-2026-pwn-67-revenge/public/output.txt` (`32d4e2203bef9e39cbe48b5499b1a541d96fc379353b122ec8a9c6e6626cf882`, 330 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2026-pwn-67-revenge/writeups/README.md` (`07cc4248fd6b2feb1b3444f1fb0a04a3d66cc22f09035e230dbe8fca86164cdd`, 2433 bytes)
  - P (2):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2026-pwn-67-revenge/solve/solve.py` (`1769781439bb964cc5caff4620f81f86f80a2162e89b78d0773d1b10a4c7e404`, 6947 bytes)
    - `materials/exploit/solve/solve.py` ← `work/materials/pwn-v11/saj-2026-pwn-67-revenge/solve/solve/solve.py` (`20eb3e21f3b64c7a859dc94ee59274a0efab9ac714c5c876097295a48f59db90`, 6244 bytes)
  - B (2):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2026-pwn-67-revenge/build/Dockerfile` (`52018275ed6d97ad637a9c3c766f2b4cdd423802b4be79c6b5b53d23e5e8b1b0`, 1499 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/saj-2026-pwn-67-revenge/build/docker-compose.yml` (`d72d926fc2642f4034f69236b1633c4db64cc32a2f30a78353006d75cdb2fe18`, 191 bytes)

### 4. `gh-9cfba69f8c90cb227725477e` — Medium-Choc-Shop

- Identity: INCTFj Finals / 2024 / Pwn
- Source: `teambi0s/INCTFj_Finals_2024-25`; `https://github.com/teambi0s/INCTFj_Finals_2024-25/tree/6050e6ee77d550c0a369513f70a275cc1f69113c/Pwn/Medium-Choc-Shop`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `prebuilt_rehost`; `system_libc`; `format_string`, `heap`, `stack_rop`
- Selection reason: fills build_form:dockerfile; fills build_mode:prebuilt_rehost; fills complexity:small; fills exploit:format_string; fills exploit:heap; fills exploit:stack_rop; fills runtime:system_libc; fills year_bucket:2024; adds event INCTFj Finals; adds source teambi0s/INCTFj_Finals_2024-25
- Material fingerprint: `d0b5b72519d6ac55bee98b876c1a2f87d95b994e39f3a382fb26574b55b81ef2`
- Material paths:
  - A (2):
    - `materials/attachments/Handout/Choc_Shop/README.md` ← `work/materials/pwn-v11/gh-9cfba69f8c90cb227725477e/public/Handout/Choc_Shop/README.md` (`ce52c8073000476c6cdc284bb8dfd5fdceac8daee45f96c77fcc7ff47b6a0537`, 114 bytes)
    - `materials/attachments/Handout/Choc_Shop/src/Choc_Shop` ← `work/materials/pwn-v11/gh-9cfba69f8c90cb227725477e/public/Handout/Choc_Shop/src/Choc_Shop` (`27c62cc8382c1376d2e849b07e6918f6336b93c8c2a80632b89742a21f1fba83`, 16864 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/admin/exp.py` ← `work/materials/pwn-v11/gh-9cfba69f8c90cb227725477e/solve/admin/exp.py` (`fd7ebfab8fa001678b36edb13403d2c89a8f3e36bdf32ed26844f4a33f2f9ca4`, 2471 bytes)
  - B (1):
    - `materials/deployment/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-9cfba69f8c90cb227725477e/build/deployment/Dockerfile` (`a26dc3d7a55ca49f0a2dc11c139a449d5f1413deb75b6b888237e5ff7b473939`, 299 bytes)

### 5. `saj-2022-pwn-data-eater` — data-eater

- Identity: DiceCTF / 2022 / Pwn
- Source: `dicegang/dicectf-2022-challenges`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/DiceCTF/2022/pwn/data-eater`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `system_libc`; `format_string`, `stack_rop`
- Selection reason: fills build_form:dockerfile; fills build_mode:hybrid; fills complexity:medium; fills exploit:format_string; fills exploit:stack_rop; fills runtime:system_libc; fills year_bucket:2022; adds event DiceCTF; adds year 2022; adds source dicegang/dicectf-2022-challenges
- Material fingerprint: `5d310711ef493c88fac5cd1125f1aaf188690b7eb17a61528603043fccb109ef`
- Material paths:
  - A (5):
    - `materials/attachments/challenge.yml` ← `work/materials/pwn-v11/saj-2022-pwn-data-eater/public/challenge.yml` (`ae1d5aaa08619349787dfdff2df7888670d5a799b6d981a4563e09a94cfec70b`, 363 bytes)
    - `materials/attachments/dataeater` ← `work/materials/pwn-v11/saj-2022-pwn-data-eater/public/dataeater` (`8d9633cc8c8c50abd336f82a6f130793837e1c14c36f301b06e923e94baaf534`, 8472 bytes)
    - `materials/attachments/libc6_2.31-17_amd64.so` ← `work/materials/pwn-v11/saj-2022-pwn-data-eater/public/libc6_2.31-17_amd64.so` (`cd235ef73f333e57baa744a58ff91af7203b735dc2166531fed7c686a1589242`, 1839792 bytes)
    - `materials/attachments/main.png` ← `work/materials/pwn-v11/saj-2022-pwn-data-eater/public/main.png` (`f532f9e742bf7ef393ee1b04ee6d897b3bcf126008adcaad5992dfebe217cbf9`, 86705 bytes)
    - `materials/attachments/run.c` ← `work/materials/pwn-v11/saj-2022-pwn-data-eater/public/run.c` (`09ae7a2b33cfe810b357acaf4f9c2c98f0d66357cd483dfde60dd10f499511b9`, 318 bytes)
  - W (2):
    - `materials/writeups/DiceCTF_2022.md` ← `work/materials/pwn-v11/saj-2022-pwn-data-eater/writeups/DiceCTF_2022.md` (`66cca4dec927358ae5afda1d47b3a976c7207fde78f083266416082274e3bea5`, 97525 bytes)
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2022-pwn-data-eater/writeups/README.md` (`019fe92c4d71650c7621981a0ceac3365370942e8e02540c86ca9bcb17881476`, 11457 bytes)
  - P (5):
    - `materials/exploit/exp.py` ← `work/materials/pwn-v11/saj-2022-pwn-data-eater/solve/exp.py` (`ffdaf0fddc0963d5a5bba34fe1ad03e113706b16adf24efc40081c47b6b82d51`, 410 bytes)
    - `materials/exploit/exploit.py` ← `work/materials/pwn-v11/saj-2022-pwn-data-eater/solve/exploit.py` (`cd8583b0bb7d68f46760e77415abac49456c4acb15c227d51263d6d2a6ec85b9`, 5603 bytes)
    - `materials/exploit/exploit_dataeater.py` ← `work/materials/pwn-v11/saj-2022-pwn-data-eater/solve/exploit_dataeater.py` (`694c8f271db1d928f63b5d6fdfaff5026abb609331019b1e0e1056368da93606`, 1621 bytes)
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2022-pwn-data-eater/solve/solve.py` (`213dcd29241f4a3c0a42ac9f437dc6012b96d12f46b0c7719688ba944df5e068`, 2451 bytes)
    - `materials/exploit/solve_detail.py` ← `work/materials/pwn-v11/saj-2022-pwn-data-eater/solve/solve_detail.py` (`79a8763f976c831c724ff34f09612e89c9c3f1f6d287816fc507555e201f46a6`, 3073 bytes)
  - B (2):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2022-pwn-data-eater/build/Dockerfile` (`cfcab6cad6e953f9b56e6e358d0baa1e64cfaa07cbdb0d7124e684e0ea7dcbed`, 209 bytes)
    - `materials/deployment/run.sh` ← `work/materials/pwn-v11/saj-2022-pwn-data-eater/build/run.sh` (`1e78c756ad120b79309ff7381f5234b67020de06990b3e4d89337c5810710101`, 94 bytes)

### 6. `gh-067edee0402ab57a169029ae` — web-pwn

- Identity: Intechfest / 2023 / Pwn
- Source: `dimasma0305/My-CTF-Challenges`; `https://github.com/dimasma0305/My-CTF-Challenges/tree/4873f89cbd243cf7edc324ad56e919dadfa33ecd/Intechfest-2023/PWN/web-pwn`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `bundled_libc_only`; `stack_rop`
- Selection reason: fills build_form:dockerfile_compose; fills build_mode:hybrid; fills complexity:medium; fills exploit:stack_rop; fills runtime:bundled_libc_only; fills topology:multi_service; fills year_bucket:2023; adds event Intechfest; adds year 2023; adds source dimasma0305/My-CTF-Challenges
- Material fingerprint: `0ebad37dd7e5f1d987ba80bb992045fe6981682c960bf46e27671bbd3b5530d3`
- Material paths:
  - A (8):
    - `materials/attachments/404.html` ← `work/materials/pwn-v11/gh-067edee0402ab57a169029ae/public/404.html` (`19553d913a423e5eac6c67533813ff295816f6d5a2e65cf955776e1a1650fb1c`, 820 bytes)
    - `materials/attachments/chall` ← `work/materials/pwn-v11/gh-067edee0402ab57a169029ae/public/chall` (`417bff60c4db7c3b0263a999883df03a9316c8dda1482fe97e4efb35364ece0d`, 23000 bytes)
    - `materials/attachments/http.c` ← `work/materials/pwn-v11/gh-067edee0402ab57a169029ae/public/http.c` (`6f650ea870baf6aeacfa1cfbc47d97efe1bdf7044eb42f9b2d4092f2fa81e826`, 5260 bytes)
    - `materials/attachments/http.h` ← `work/materials/pwn-v11/gh-067edee0402ab57a169029ae/public/http.h` (`3e73eef119ba5f9c749bc5c2cb15270f97abc7d1ff7f8c90e6424667a2904ce4`, 1907 bytes)
    - `materials/attachments/index.html` ← `work/materials/pwn-v11/gh-067edee0402ab57a169029ae/public/index.html` (`5269df521a0d5861a8c61ac52b1b437fe4a727a832387abc19c4fb56e9b2501c`, 831 bytes)
    - `materials/attachments/libc.so` ← `work/materials/pwn-v11/gh-067edee0402ab57a169029ae/public/libc.so` (`fdaa44be131da64b35f6b132cbb612e0acdd49ca0d29fd247d023619835231e4`, 6616616 bytes)
    - `materials/attachments/main.c` ← `work/materials/pwn-v11/gh-067edee0402ab57a169029ae/public/main.c` (`d0d502d28a8f7c32b630ebf9c15220bdd14deadfbba1c5d10437cfd9ece27160`, 1751 bytes)
    - `materials/attachments/settings.json` ← `work/materials/pwn-v11/gh-067edee0402ab57a169029ae/public/settings.json` (`1534c539f4e72b5510c6a5f2df00273e02147d18cd60b120172bac3c94fb26dd`, 125 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solver/solve.py` ← `work/materials/pwn-v11/gh-067edee0402ab57a169029ae/solve/solver/solve.py` (`9ffe83d777448b6a9ce82fbd5ff1cbd0488c4fb9fab09911360c2c3c9aff4ffc`, 4867 bytes)
  - B (7):
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/gh-067edee0402ab57a169029ae/build/docker-compose.yml` (`379086443fea6c4ebd5f41cb81f1a5f099a8debefc9ef784491b003ed21ec783`, 338 bytes)
    - `materials/deployment/neko/CMakeLists.txt` ← `work/materials/pwn-v11/gh-067edee0402ab57a169029ae/build/neko/CMakeLists.txt` (`ecfe2a6b731f84e00f63abf873301a97975df528cddf97b600b0f8021a20d686`, 122 bytes)
    - `materials/deployment/neko/Dockerfile` ← `work/materials/pwn-v11/gh-067edee0402ab57a169029ae/build/neko/Dockerfile` (`a37b7636cdb72c89ce633545fe355e46cdfb4c8cbb1711bda38b50b80b772c37`, 324 bytes)
    - `materials/deployment/neko/Makefile` ← `work/materials/pwn-v11/gh-067edee0402ab57a169029ae/build/neko/Makefile` (`84fd4f697039c8cf58440e2a7b6eabe32af1a52121f96b2ce9c4861c6a6c0769`, 260 bytes)
    - `materials/deployment/neko/http.c` ← `work/materials/pwn-v11/gh-067edee0402ab57a169029ae/build/neko/http.c` (`6f650ea870baf6aeacfa1cfbc47d97efe1bdf7044eb42f9b2d4092f2fa81e826`, 5260 bytes)
    - `materials/deployment/neko/http.h` ← `work/materials/pwn-v11/gh-067edee0402ab57a169029ae/build/neko/http.h` (`3e73eef119ba5f9c749bc5c2cb15270f97abc7d1ff7f8c90e6424667a2904ce4`, 1907 bytes)
    - `materials/deployment/neko/main.c` ← `work/materials/pwn-v11/gh-067edee0402ab57a169029ae/build/neko/main.c` (`d0d502d28a8f7c32b630ebf9c15220bdd14deadfbba1c5d10437cfd9ece27160`, 1751 bytes)

### 7. `saj-2021-pwn-kqueue` — Kqueue

- Identity: InCTF / 2021 / Pwn
- Source: `teambi0s/InCTFi`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/InCTF/2021/pwn/Kqueue`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `source_build`; `unknown_or_non_elf`; `heap`, `kernel`, `shellcode_seccomp`
- Selection reason: fills build_form:dockerfile_compose; fills build_mode:source_build; fills complexity:medium; fills exploit:kernel; fills year_bucket:2020_2021; adds event InCTF; adds year 2021; adds source teambi0s/InCTFi
- Material fingerprint: `6b702669c2cf80f48c96e706db35e4c1a13970f33ff24b1230c5e18277730a9e`
- Material paths:
  - A (8):
    - `materials/attachments/bzImage` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/public/bzImage` (`10a263e7d80b0a4fe3c96e28277b0d6966b5caab8d5264a6c949f635d7e5a988`, 8948224 bytes)
    - `materials/attachments/chall` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/public/chall` (`678a56853da9cd63b2e5842eb3221eb4398474b4e6f7a557a8f14a2dbc780c2f`, 253 bytes)
    - `materials/attachments/chall.437fffc1` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/public/chall.437fffc1` (`cdeb4a2c7d528273cf297e3fbce9a698ca90e70fbf1fa30bc7d6ee54a1c232af`, 252 bytes)
    - `materials/attachments/kqueue.c` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/public/kqueue.c` (`046ca3be1d8a31598b3c3c61fd8bd2417c1bf59a4afbb1b0703ba2c57b05ab28`, 7812 bytes)
    - `materials/attachments/rootfs.79bc6e53.cpio` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/public/rootfs.79bc6e53.cpio` (`c1bd8f9b9d51d2f1d21735c81f5878804cade88549d2b64a65b907509def9b10`, 1489920 bytes)
    - `materials/attachments/rootfs.cpio` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/public/rootfs.cpio` (`24199932ed1d022974b1b3c36174d40da81079ef4be0f56ac5eac637dabba628`, 1489920 bytes)
    - `materials/attachments/src/kqueue.c` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/public/src/kqueue.c` (`bcfc6ee99d593b4e9922f8a2ca9161c8494b5b2d023ce846f9acaf4e87da6c16`, 7812 bytes)
    - `materials/attachments/src/kqueue.h` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/public/src/kqueue.h` (`5a5b0a7305dcd4ec265185befa2e01c4ecbecca1b272dbf6aba0c3d5007f54e0`, 2626 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/writeups/README.md` (`a004b8515632b5b4a6099983097f862348ae5bdea689c73ee857eeaab65ac21a`, 660 bytes)
  - P (4):
    - `materials/exploit/Admin/exp` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/solve/Admin/exp` (`ee55bd1e1999e1d679ffe9c833dfdb5c44f5985bf69a41ff3e3c6ecc71e3fd01`, 887248 bytes)
    - `materials/exploit/Admin/exp.c` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/solve/Admin/exp.c` (`83993830ac49b2cad28bcfc96d3c2239eb480f67b1ee8dd03c29791efd2b1765`, 5732 bytes)
    - `materials/exploit/Admin/exp.py` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/solve/Admin/exp.py` (`03f048460d72f8014007bcee24c8c6ef5559c3bc08a3d9dcb9be7b89102686d1`, 1137 bytes)
    - `materials/exploit/exp.c` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/solve/exp.c` (`7ce8b889569bdd376b9a220fee39555f4cf9437c205644c6270e96bd2853e45e`, 3457 bytes)
  - B (7):
    - `materials/deployment/Admin/src/kqueue.c` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/build/Admin/src/kqueue.c` (`bcfc6ee99d593b4e9922f8a2ca9161c8494b5b2d023ce846f9acaf4e87da6c16`, 7812 bytes)
    - `materials/deployment/Admin/src/kqueue.h` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/build/Admin/src/kqueue.h` (`5a5b0a7305dcd4ec265185befa2e01c4ecbecca1b272dbf6aba0c3d5007f54e0`, 2626 bytes)
    - `materials/deployment/Admin/start.sh` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/build/Admin/start.sh` (`1a71e07055d3bf386f38a989943b35b38e24963456589d86f082ceae59db82a0`, 266 bytes)
    - `materials/deployment/Chall_Host/Dockerfile` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/build/Chall_Host/Dockerfile` (`91076d72c02a1501abba1460e152dc60b3ccd0842b2932f8b46ae748c54ade01`, 647 bytes)
    - `materials/deployment/Chall_Host/docker-compose.yml` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/build/Chall_Host/docker-compose.yml` (`e3dd1649d9f5635c94293ec2bdbfc45fa46a6b9e1face1eba84c61834d635a6d`, 170 bytes)
    - `materials/deployment/Chall_Host/run.sh` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/build/Chall_Host/run.sh` (`0ff96d01eb14ccb17e9d008fd32fea90c677f4b1193dbfbc9ca234252ac850f2`, 52 bytes)
    - `materials/deployment/Chall_Host/start.sh` ← `work/materials/pwn-v11/saj-2021-pwn-kqueue/build/Chall_Host/start.sh` (`8ac2a7b5f63c8a289ee133dd9a0fe30f6463a926eff9ee2d891ba71a0a0acdf7`, 89 bytes)

### 8. `saj-2025-pwn-cursed-format` — cursed_format

- Identity: PatriotCTF / 2025 / Pwn
- Source: `MasonCompetitiveCyber/PatriotCTF2024`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/PatriotCTF/2025/pwn/cursed_format`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `source_build`; `bundled_libc_loader`; `stack_rop`
- Selection reason: fills build_form:dockerfile; fills build_mode:source_build; fills complexity:medium; fills runtime:bundled_libc_loader; fills year_bucket:2025_plus; adds event PatriotCTF; adds year 2025; adds source MasonCompetitiveCyber/PatriotCTF2024
- Material fingerprint: `6832edd86f8e0c5bbc6db0a042dc8f3cd5dc534082c4af7efb9d453cf7596aad`
- Material paths:
  - A (8):
    - `materials/attachments/brute_stack.py` ← `work/materials/pwn-v11/saj-2025-pwn-cursed-format/public/brute_stack.py` (`605d2110528e963c6d541dfe87ecbb11fdec32aae7206c278c36a16b8f062d10`, 2119 bytes)
    - `materials/attachments/cursed_format.py` ← `work/materials/pwn-v11/saj-2025-pwn-cursed-format/public/cursed_format.py` (`ed2c9d9cfe711509863d8113d0fef14998df579bb1225649d142395d03e7974a`, 1650 bytes)
    - `materials/attachments/debug.py` ← `work/materials/pwn-v11/saj-2025-pwn-cursed-format/public/debug.py` (`82a3ac2aecdd607b45fd32f6952dfefd34758ae636acf4e6676501b956ce33ee`, 2294 bytes)
    - `materials/attachments/fuzz.py` ← `work/materials/pwn-v11/saj-2025-pwn-cursed-format/public/fuzz.py` (`59289c84a95fc22a2d68aa91481bc44e1365d1dbf132e52cf3f017af888c3a24`, 2499 bytes)
    - `materials/attachments/ld-2.31.so` ← `work/materials/pwn-v11/saj-2025-pwn-cursed-format/public/ld-2.31.so` (`1c654e88d721c9ac659b48400d20b5310ead8c6d15eeaf695d507d00d59ef490`, 177928 bytes)
    - `materials/attachments/leak_check.py` ← `work/materials/pwn-v11/saj-2025-pwn-cursed-format/public/leak_check.py` (`0a69c7d07b8f9212a775323fd60f191425bccb8830f8f904bdf488bd97b8c6ce`, 2011 bytes)
    - `materials/attachments/libc-2.31.so` ← `work/materials/pwn-v11/saj-2025-pwn-cursed-format/public/libc-2.31.so` (`c9de975636abd825d1ea9cad375a2fc3b005a6517176bf99b172817fe3321efd`, 1901536 bytes)
    - `materials/attachments/src/cursed_format.c` ← `work/materials/pwn-v11/saj-2025-pwn-cursed-format/public/src/cursed_format.c` (`71272190f85354f5136de43b0b5b924f9e3c2dfcaf2af7e41efc112ff45e3659`, 1354 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2025-pwn-cursed-format/solve/solve.py` (`52e6ba69729c398f6407013a2a9c9c08da4fd62b46cc1134ad38ecce06fe51df`, 3895 bytes)
  - B (7):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2025-pwn-cursed-format/build/Dockerfile` (`811a93df86b1fe7c1567dccd89cd400bc3afbc393e420408e68b41f9afd93316`, 612 bytes)
    - `materials/deployment/Makefile` ← `work/materials/pwn-v11/saj-2025-pwn-cursed-format/build/Makefile` (`62c07b045ad5b62ac1d847476d4b491d45a722c53bdfb0862c21eec99f58284b`, 117 bytes)
    - `materials/deployment/brute_stack.py` ← `work/materials/pwn-v11/saj-2025-pwn-cursed-format/build/brute_stack.py` (`605d2110528e963c6d541dfe87ecbb11fdec32aae7206c278c36a16b8f062d10`, 2119 bytes)
    - `materials/deployment/cursed_format.c` ← `work/materials/pwn-v11/saj-2025-pwn-cursed-format/build/cursed_format.c` (`71272190f85354f5136de43b0b5b924f9e3c2dfcaf2af7e41efc112ff45e3659`, 1354 bytes)
    - `materials/deployment/debug.py` ← `work/materials/pwn-v11/saj-2025-pwn-cursed-format/build/debug.py` (`82a3ac2aecdd607b45fd32f6952dfefd34758ae636acf4e6676501b956ce33ee`, 2294 bytes)
    - `materials/deployment/fuzz.py` ← `work/materials/pwn-v11/saj-2025-pwn-cursed-format/build/fuzz.py` (`59289c84a95fc22a2d68aa91481bc44e1365d1dbf132e52cf3f017af888c3a24`, 2499 bytes)
    - `materials/deployment/leak_check.py` ← `work/materials/pwn-v11/saj-2025-pwn-cursed-format/build/leak_check.py` (`0a69c7d07b8f9212a775323fd60f191425bccb8830f8f904bdf488bd97b8c6ce`, 2011 bytes)

### 9. `saj-2024-pwn-xss-finder-tool` — XSS_Finder_Tool

- Identity: 1337UP / 2024 / Pwn
- Source: `intigriti/CTF`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/1337UP/2024/pwn/XSS_Finder_Tool`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `static`; `shellcode_seccomp`, `stack_rop`, `vm_emulator`
- Selection reason: fills build_form:dockerfile_compose; fills build_mode:hybrid; fills complexity:large; fills runtime:static; fills topology:multi_service; fills year_bucket:2024; adds event 1337UP; adds source intigriti/CTF
- Material fingerprint: `cadbe33afd99856b8ff07afb8caf680a6fe243c77388faad9cb556b060d23206`
- Material paths:
  - A (89):
    - `materials/attachments/xss_finder/chrome/chrome-linux/ClearKeyCdm/_platform_specific/linux_x64/libclearkeycdm.so` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/ClearKeyCdm/_platform_specific/linux_x64/libclearkeycdm.so` (`4e47454d22a22d226dd66259f105edaa93f3c8010baf32692e7c66a7f7eae53b`, 10099704 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/MEIPreload/manifest.json` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/MEIPreload/manifest.json` (`44844cf3dde6e80087ae0e6bf0d9326d7ef7d23326d24ac83af0850be26923d2`, 238 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/MEIPreload/preloaded_data.pb` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/MEIPreload/preloaded_data.pb` (`c6070a157b4e28d16fbccbd233e93846ddb070c85e1a1bc64469b7a5f1424fad`, 8254 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/chrome-wrapper` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/chrome-wrapper` (`17b0432a26e628287789f1efa53056384a46b6265939e8bf819b1b6cf8472ada`, 5061 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/chrome_100_percent.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/chrome_100_percent.pak` (`60b6f843c335731eefd0fa495afbefaa6f88894292dc6af1b424a998e9ac221e`, 652205 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/chrome_200_percent.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/chrome_200_percent.pak` (`0ebd910123e2dab5ac0332beb06a13535ceb0c7faaf593178f31a80ab25352bb`, 1011954 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/chrome_crashpad_handler` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/chrome_crashpad_handler` (`4368438d261b88eb1a1c342bdc0b252eb3015f81dfd8c7edcf4794b9bd0bd3f2`, 2021656 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/chrome_sandbox` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/chrome_sandbox` (`9c8423a37338b10fdf010ea9c15498c5f2bd5b973403a7172b7ea67859e292d9`, 355592 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/icudtl.dat` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/icudtl.dat` (`f5170aa2b388d23bebf98784dd488a9bcb741470384a6a9a8d7a2638d768defb`, 10717392 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/libEGL.so` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/libEGL.so` (`9b36ef89174d127fdb209b5e1ea944b13ab862740622b77df77698e68c94470e`, 410920 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/libGLESv2.so` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/libGLESv2.so` (`2c81298ee14382bc5ef9a03098b21d4b384e164f8f3c3cde040e1e068a00e6b5`, 9509584 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/libvk_swiftshader.so` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/libvk_swiftshader.so` (`b2233aaf3c29d50b2bbd1ab6de47cc97814930b8debf29a3a8c57b9d329d67d6`, 6428248 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/libvulkan.so.1` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/libvulkan.so.1` (`09c20f2afae59ebe57f62f42a405f9747d8557cdc4eb2cf6f094664c47c03e48`, 917160 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/af.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/af.pak` (`f96c1809a8af4403a0ca355afb116d00499b11ec85c6aa6c8f391915f42c7252`, 467703 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/af.pak.info` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/af.pak.info` (`67bc2f3360cfc999b021125af1dbb8656e37e3fcc9189a65048f0ebc00e8ac05`, 981750 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/am.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/am.pak` (`23abf1ddeb71aed3f4951a1eec44d819cc236cbfd6f1a5f0bb136802a8aae27e`, 755962 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/ar-XB.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/ar-XB.pak` (`37ed63058cfe21f6ad1a415df06fc574938fe9877e056fe995911055d5f2d35a`, 765147 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/ar.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/ar.pak` (`d02530217973e4c8f7b29675b4a8248e7672a951ced246703d22863d370811a8`, 832889 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/bg.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/bg.pak` (`f917b67a4eba799d77176b9404454a6ff3ecf53e117b30a8ca79b7299792675c`, 859536 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/bn.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/bn.pak` (`8370c045991b83cff4f897b598c118ab387f22ae80ae42c6589d2182425309eb`, 1107088 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/ca.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/ca.pak` (`147276978622d3c0efa9f37cd89d7afed5adcda1d961676f26d306d0346404d6`, 533622 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/cs.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/cs.pak` (`c8e728c304623985b5d65bbdb89efbb94393f6888cac2b3fef34255881e4d29b`, 541099 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/da.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/da.pak` (`36e30979cd94310cf2fa25116132bce09e8f9c16ea87600933ae02ce4fa0ba5c`, 493312 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/de.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/de.pak` (`973e8696b25fd8fdb7f59d2033ea67e2652baaadd1a544f333f7f65c8229a5d0`, 530675 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/el.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/el.pak` (`1cf986c1878e9fa35ca16698bd672495d45dedf725e069bfff8d08ab09ce04b4`, 942069 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/en-GB.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/en-GB.pak` (`445cbfb7bb69d9b42847ee023a5aa449fabeff08ba0559073e39a83a573009da`, 428604 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/en-US.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/en-US.pak` (`52c3e8841ffb17e54b341fa5a523bb7f51345c4897b5acdd7dddc40a097fa174`, 432678 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/en-XA.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/en-XA.pak` (`5f14d7573d070660eb9fcd70cbe940bac5513207368d8fd6f223c2caa68b86d7`, 959386 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/es-419.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/es-419.pak` (`c0bd9e955d311b7286b13cbc9f963e60bf40c145cb94ed159454012e23006e0a`, 521708 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/es.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/es.pak` (`41eb0f527125de94e79ca637f458b8d02fb2818f33b2ead0ddd21a3e624fc8ef`, 520250 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/et.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/et.pak` (`292ce5a389d1c88dee18e08f249dd032795e2d202d275553aafb2f6bb7855240`, 472756 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/fa.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/fa.pak` (`0a256f306b6625f0104d5c588b10e0afacfe1931809526b1efbe91191b9fc834`, 766871 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/fi.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/fi.pak` (`5330f4deb4c72f6f3e9e6f6506687d2a4b2a56eba13837b9be2d4af2320a6635`, 479993 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/fil.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/fil.pak` (`14a14a93a065610a51b9167cfd936ef3888ea1f3d42bc594fd7948993708fa32`, 543557 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/fr.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/fr.pak` (`8ef6435d86ca1a6a7065603d380b1ba4c41f48b29f065d1003ae202ffc7d4388`, 564975 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/gu.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/gu.pak` (`2d17e9cf67b5d0ad501832bb7833bb00b6529f0efaeedac81eded4c4948ab4f2`, 1089147 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/he.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/he.pak` (`b46bb066acdd8f82dad18d84b091b702ebda974708137e585d3366746e90f3b9`, 676568 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/hi.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/hi.pak` (`24a0d345ab3b44413ac2d861a6848f269081022c68322ff3cb0613de538c21fa`, 1150913 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/hr.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/hr.pak` (`dc7f5bc89aa29afe3d11061c78391f53b83b68ef432d2a8225b887d8e4cad87a`, 523902 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/hu.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/hu.pak` (`9c54400a54768532fd350a8170267cef72d78de8dbafbef1fad6b8ebd3e0ffa7`, 561688 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/id.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/id.pak` (`afb3172f2b26e3d3a53e6164158346c4378652fe38b9a19fa92387db6babf0b8`, 463831 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/it.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/it.pak` (`fc3e9f15304e5862d2b3fdef943764ef837522076e2d2cfd947e81b5d4d83c4d`, 519081 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/ja.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/ja.pak` (`4c49e3489d6b5395c0b27e071293c3ccd9a2aeab2ff68bd677c453d1e142cdf1`, 627625 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/kn.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/kn.pak` (`63c2bc3f38d1cc9a41c954e56a894d149c75e48ee84776c75a250bf9ae904bf5`, 1243523 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/ko.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/ko.pak` (`b639f920d9a23255b291cbf7bbd06f218d2e94176561f290ba660fd63af4fc30`, 527448 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/lt.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/lt.pak` (`7e1010eba2fae4b616cd684677020e9364638fb982f42a141f3a7cefc91a1f5a`, 570850 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/lv.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/lv.pak` (`1f800632ef9e0578aaf07ae391ec1c3553b3a9be703b8281b401820572cf52b0`, 566805 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/ml.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/ml.pak` (`2b9eb5c9426356d700e2f267ba91e68e106cc48fea22edbd33bf067e2e7a45ea`, 1289653 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/mr.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/mr.pak` (`5c3eb15af62ad4f6a2c9dfef66197e6d4765abd34cb1e086ce939b38dbd695f7`, 1061405 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/ms.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/ms.pak` (`d6dc3ca2957407c18af8785127dd91d0f0042708f206981d8ec61a94be1c6b5a`, 485742 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/nb.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/nb.pak` (`672c1bd6ee836d34b7b9194e9bd9fd01005e78c85ee5241ecf1fce7559392a88`, 472914 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/nl.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/nl.pak` (`ac9d8f33ecf7feb6dbed6a5c4c9b084abda36337fa2f5741cac7c4c9ae02d536`, 488240 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/pl.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/pl.pak` (`fe5248be0fbc1a635d87e775c27d25af2fcea22d4a6f3bb9255e9dbaa3d09074`, 547133 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/pt-BR.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/pt-BR.pak` (`1cd867ce93a23f29cb95af70cfa442c9f00ad5ad8ab6e1c28293d43c3626c6c1`, 513104 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/pt-PT.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/pt-PT.pak` (`84e45baf85a75577765b3e15a330543ac31f06cd53ae95c17bd810a04e90259c`, 515530 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/ro.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/ro.pak` (`408fe7349c2955c2005f67c5d09907dad1e40d377727972881db0923a36ad896`, 533445 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/ru.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/ru.pak` (`132cdba0d63237a36e509345eb89b08a267fc0e6da5323511af5335669c0132f`, 872318 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/sk.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/sk.pak` (`8943106fdf130ebb0f49439b1262b9e1fe351842589263ffededa98fba2abaab`, 550494 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/sl.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/sl.pak` (`ea334d481b5cbff936806c68519be2d10cf37928feeb455dd6c4ed49325cb80e`, 529703 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/sr.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/sr.pak` (`2ce509d0879de293998addf2ba08018f67b7cdb79858e46bbe174f48c20ace42`, 810557 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/sv.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/sv.pak` (`e4f80d0a02ffe0870932fce455968efd7bd0d24f542ced3b361e5da235739789`, 476852 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/sw.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/sw.pak` (`876ca60c589d23780454d66066ba1f3dd12f798889ed242c254c075d21610d12`, 501135 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/ta.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/ta.pak` (`af961d1ffd54bf18d34989777a74f8bdb27f7336dfa49ff06089ed9bd0c23e45`, 1282237 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/te.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/te.pak` (`8e9404cdbb04cfe90c24744925af4bb0cc2b31478eb96e1ff7df1d7bd52cdb6e`, 1182162 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/th.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/th.pak` (`058ab47274b091f46a02a6cadce77caf9c2cd4f395e75553ec7a55547a70b573`, 999320 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/tr.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/tr.pak` (`b632d89cb5bedea76a2e0fba8619611f9a33335e1b98da6595fc7f921acb9f41`, 510883 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/uk.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/uk.pak` (`2879c847623812f18bd6408f2af2c434f1c6af12a57fdd9df4364b6cfa571b77`, 868801 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/ur.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/ur.pak` (`5e870719bbd0cfd53ef9aedb4862c5d95e6ea31b862fc5fafd84390604140012`, 757624 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/vi.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/vi.pak` (`b787282619d7fd5f356c0ffeb95587d9f66f393077a1590cea07631a64bc31e5`, 604653 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/zh-CN.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/zh-CN.pak` (`b7dfe77de056815cab9c5cd814829e1a701011bac074e940ba2b56da40708b10`, 438800 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/locales/zh-TW.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/locales/zh-TW.pak` (`27b61c35f056d44f840efaffd7ceead3ba483a56dc02789793ac107b222bba49`, 436983 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/nacl_helper` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/nacl_helper` (`17c8c0e75d73a047ef6a31a8406351c9da9f461f9517140cfce84fc81aa81284`, 5321096 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/nacl_helper_bootstrap` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/nacl_helper_bootstrap` (`8de9f8ab5bab89d72a997c29c902ed9691eca0da0be0d06f1db968444eb9c58a`, 9752 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/nacl_irt_x86_64.nexe` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/nacl_irt_x86_64.nexe` (`efc86c4b94f4c33ed02884ad936443dbf0476fd7bfbfb281bfb4c4e8c713dc1d`, 4589008 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/product_logo_48.png` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/product_logo_48.png` (`21b2927bb47d305bbda718b9c08c6b51fbc0597454587978ea0046bc595393fb`, 2531 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/resources.pak` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/resources.pak` (`d34e51ad48cf43b443922d88dda189f0f81c5516c58cfd9a73996731c8872fc5`, 9240911 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/resources/inspector_overlay/inspector_overlay_resources.grd` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/resources/inspector_overlay/inspector_overlay_resources.grd` (`68760fc7002c3999d3b2ac6eb80febe28182134a0dd1d53829f660b3d96bc9ef`, 532 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/resources/inspector_overlay/main.js` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/resources/inspector_overlay/main.js` (`4fb2347ed098ff9494b8a4f15239cd5068fc21d8ded35b31874dafa1e93bb3eb`, 71384 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/v8_context_snapshot.bin` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/v8_context_snapshot.bin` (`e4c3cdf1cc6b386ac164214f965f1b5ee1230ad190098474324073b037959571`, 626313 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/vk_swiftshader_icd.json` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/vk_swiftshader_icd.json` (`c9eef28b6b984fec220ef0abfecc40b502d46946706e47bfe97707027cb818bd`, 107 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/xdg-mime` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/xdg-mime` (`ad2d5802bb3604daa849ce5ac86a81acf7548c8ffd10ab4ecae1d56a5f10d63b`, 37394 bytes)
    - `materials/attachments/xss_finder/chrome/chrome-linux/xdg-settings` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/chrome/chrome-linux/xdg-settings` (`442777b1f7d206c5ff661fea00dc1a8319df6256feccc54f186f6edacf235801`, 33273 bytes)
    - `materials/attachments/xss_finder/web/app.py` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/web/app.py` (`1ce67f14d2a4ee6893acb0bc90156f252bf621f4f5181cd3ee598e8cc869f0d6`, 1258 bytes)
    - `materials/attachments/xss_finder/web/requirements.txt` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/web/requirements.txt` (`5fb555d2ebed138f045b556e6da9118198f9aef99de326281953e16e7562cb92`, 29 bytes)
    - `materials/attachments/xss_finder/web/static/main.css` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/web/static/main.css` (`a4fe13e212c662a50fda75e09526d7f574074e678641affa084279d54af0573a`, 209 bytes)
    - `materials/attachments/xss_finder/web/templates/dashboard.html` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/web/templates/dashboard.html` (`e0b57aa5cb4bf7945e1cbc474e45666b3dcd87427ee714ff54d0fb1224d41bee`, 63872 bytes)
    - `materials/attachments/xss_finder/web/templates/footer.html` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/web/templates/footer.html` (`ea8d4e50f57cffc468034f28e43803c8ff0283417bceb05c6a4da970747cac5b`, 105 bytes)
    - `materials/attachments/xss_finder/web/templates/header.html` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/web/templates/header.html` (`8eeb6536438842d828a04db0ae95a88c2207a9d0ca38e58eb17a46097f2952c0`, 2891 bytes)
    - `materials/attachments/xss_finder/web/templates/scan.html` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/public/xss_finder/web/templates/scan.html` (`12659b74b70301d501cc91d7ea64da589867c1f653549e889692dfe79cfca1e4`, 2801 bytes)
  - W (2):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/writeups/README.md` (`e06d11e3879e58fa11632b668e30525e2416e625f262276864b4e9d358f9c509`, 60 bytes)
    - `materials/writeups/exp.html` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/writeups/exp.html` (`4f9ebda774d1f9d98d3cd0710f1000d28ca8ea5d2c89c3aac30178ea30918e8b`, 10795 bytes)
  - P (5):
    - `materials/exploit/autopwn.py` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/solve/autopwn.py` (`3cb7aae9de5060bd1ba553d8b0b5504e060b19ec7ea26752390a3547988e4f52`, 4678 bytes)
    - `materials/exploit/solution/generate_shellcode/exp.wasm` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/solve/solution/generate_shellcode/exp.wasm` (`ac8aded476a58bb75b86003dd835ca042d0aa80f1d746ff1afa46f7b7375edc3`, 716 bytes)
    - `materials/exploit/solution/generate_shellcode/exp.wat` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/solve/solution/generate_shellcode/exp.wat` (`602360039050bb141e70124d3a9c2086c7631a48be1c7746c4230680f9ea9083`, 2853 bytes)
    - `materials/exploit/solution/templates/exp.html` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/solve/solution/templates/exp.html` (`4f9ebda774d1f9d98d3cd0710f1000d28ca8ea5d2c89c3aac30178ea30918e8b`, 10795 bytes)
    - `materials/exploit/writeup.pdf` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/solve/writeup.pdf` (`e280a2672f9a8290a1c63a4691df7d3cc1ae28e6abf773b44dd51ed98ca98c44`, 1780063 bytes)
  - B (6):
    - `materials/deployment/xss_finder/chrome/Dockerfile` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/build/xss_finder/chrome/Dockerfile` (`cb6ba89ce0ff05b6ae4ef730b447f3b5d41123b1a604c12afe502ef39d200bd8`, 853 bytes)
    - `materials/deployment/xss_finder/chrome/chrome-linux/resources/inspector_overlay/main.js` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/build/xss_finder/chrome/chrome-linux/resources/inspector_overlay/main.js` (`4fb2347ed098ff9494b8a4f15239cd5068fc21d8ded35b31874dafa1e93bb3eb`, 71384 bytes)
    - `materials/deployment/xss_finder/docker-compose.yml` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/build/xss_finder/docker-compose.yml` (`85f423dd090fbfe35e62e57087e0d5944bf8a7b674d2c2014ecf224571bd1957`, 194 bytes)
    - `materials/deployment/xss_finder/start.sh` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/build/xss_finder/start.sh` (`e8fbc20d322f458698881da6db9ef6499da35257ff407bae9420f1ad8e425242`, 232 bytes)
    - `materials/deployment/xss_finder/web/Dockerfile` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/build/xss_finder/web/Dockerfile` (`713b999d71d63445a419a39c28c0f7759b4411ee9993dd5f8a12f8d9306d0c39`, 152 bytes)
    - `materials/deployment/xss_finder/web/app.py` ← `work/materials/pwn-v11/saj-2024-pwn-xss-finder-tool/build/xss_finder/web/app.py` (`1ce67f14d2a4ee6893acb0bc90156f252bf621f4f5181cd3ee598e8cc869f0d6`, 1258 bytes)

### 10. `gh-10b815656e32700eed11ec07` — vault

- Identity: Arkavidia / 2019 / Pwn
- Source: `ChaO-0/WriteUps`; `https://github.com/ChaO-0/WriteUps/tree/3ae188c1b8b2040c65377557d0495a704108d800/Arkavidia/2019/Pwn/vault`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `prebuilt_rehost`; `system_libc`; `other`
- Selection reason: fills build_form:dockerfile; fills build_mode:prebuilt_rehost; fills complexity:small; fills runtime:system_libc; fills year_bucket:pre_2020; adds event Arkavidia; adds year 2019; adds source ChaO-0/WriteUps
- Material fingerprint: `78de0d18dc35db3a251e62fb64708459cc6f2ccfb23cf072338bdbe33f1b3de7`
- Material paths:
  - A (1):
    - `materials/attachments/vault` ← `work/materials/pwn-v11/gh-10b815656e32700eed11ec07/public/vault` (`79f49345b42329a3854373b9b1e1257963c9552d878764fccda76224d4695912`, 7592 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/exploit.py` ← `work/materials/pwn-v11/gh-10b815656e32700eed11ec07/solve/exploit.py` (`99903c9fcb584aac28843a293dd373ef7bb3b837ec76b421e3873f718e741962`, 1972 bytes)
  - B (1):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-10b815656e32700eed11ec07/build/Dockerfile` (`437786d7bee39a3f151a7a8c461d7d19baeb17f8c20dbbc20c70e90f957f6d57`, 214 bytes)

### 11. `gh-4aaa3bc687f9a4ebc31dc755` — formatting-is-weird

- Identity: AtHackCTF / 2025 / Pwn
- Source: `athack-ctf/AtHackCTF-2025-Challenges`; `https://github.com/athack-ctf/AtHackCTF-2025-Challenges/tree/eeb2de0d5593f704789b1e4e41c3f37462ddf0d3/Pwn/formatting-is-weird`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `source_build`; `bundled_libc_only`; `format_string`, `stack_rop`
- Selection reason: fills build_mode:source_build; fills complexity:medium; fills runtime:bundled_libc_only; fills year_bucket:2025_plus; adds event AtHackCTF; adds source athack-ctf/AtHackCTF-2025-Challenges
- Material fingerprint: `959250e26256d4a54abcbbae472a611df5bf2f166fa68fcaa7b32a7ed5eb2f47`
- Material paths:
  - A (2):
    - `materials/attachments/libc.so.6` ← `work/materials/pwn-v11/gh-4aaa3bc687f9a4ebc31dc755/public/libc.so.6` (`c1e50a701d3245c8c45a1ba40151efe414ac41d2c9ae604087b4875e0d85c4fb`, 2125328 bytes)
    - `materials/attachments/pwnme.c` ← `work/materials/pwn-v11/gh-4aaa3bc687f9a4ebc31dc755/public/pwnme.c` (`23954ba845dd465ecf13d3313db3855ebbd6d58575d7f29ef27f7708f5f13808`, 2497 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/gh-4aaa3bc687f9a4ebc31dc755/writeups/README.md` (`b31cc3d3497b90a3d498690ad6a351e1bbc7026dee702353bc1bdeb024c6e53c`, 576 bytes)
  - P (1):
    - `materials/exploit/solution/exploit.py` ← `work/materials/pwn-v11/gh-4aaa3bc687f9a4ebc31dc755/solve/solution/exploit.py` (`ba773a637c948ffb80a1fc7cea22cd150085aa8477feb194a02628721df2d273`, 4106 bytes)
  - B (4):
    - `materials/deployment/docker-compose.yaml` ← `work/materials/pwn-v11/gh-4aaa3bc687f9a4ebc31dc755/build/docker-compose.yaml` (`666256eee3f62bca923e6a4f53def1d07327a6d42b04c638233abd5ced661205`, 156 bytes)
    - `materials/deployment/source/Dockerfile` ← `work/materials/pwn-v11/gh-4aaa3bc687f9a4ebc31dc755/build/source/Dockerfile` (`71c32df37c3cebf76a6e2ca543dbd9e1ffb7250fb38c63efd2931e87cab19798`, 736 bytes)
    - `materials/deployment/source/build.sh` ← `work/materials/pwn-v11/gh-4aaa3bc687f9a4ebc31dc755/build/source/build.sh` (`cd9023ca92208c936e4ea83eba9c436df4a118c67c3db02dae795c98106370e8`, 109 bytes)
    - `materials/deployment/source/pwnme.c` ← `work/materials/pwn-v11/gh-4aaa3bc687f9a4ebc31dc755/build/source/pwnme.c` (`23954ba845dd465ecf13d3313db3855ebbd6d58575d7f29ef27f7708f5f13808`, 2497 bytes)

### 12. `saj-2021-pwn-ebpf` — eBPF

- Identity: GoogleCTF / 2021 / Pwn
- Source: `sajjadium/ctf-archives`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/GoogleCTF/2021/pwn/eBPF`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `build_metadata`; `source_build`; `musl`; `heap`, `kernel`
- Selection reason: fills build_mode:source_build; fills complexity:large; fills runtime:musl; fills year_bucket:2020_2021; adds event GoogleCTF; adds source sajjadium/ctf-archives
- Material fingerprint: `b013e59847c7b951cc39170d26adc60df3599d1459da3480830df7833e3af50f`
- Material paths:
  - A (7):
    - `materials/attachments/bpf_verifier.h.patch` ← `work/materials/pwn-v11/saj-2021-pwn-ebpf/public/bpf_verifier.h.patch` (`a00a14c656797dc39d268e2f7c295500112775db87b86f0657f0c76ee367778b`, 368 bytes)
    - `materials/attachments/bzImage` ← `work/materials/pwn-v11/saj-2021-pwn-ebpf/public/bzImage` (`7bb4af9766aa4b3705e80d49b3e3fa152526c3e1527f55d17fb6b6624d18f938`, 13262720 bytes)
    - `materials/attachments/gen_cpio.sh` ← `work/materials/pwn-v11/saj-2021-pwn-ebpf/public/gen_cpio.sh` (`b4c45475602433d59f8d535bc2251fc8fde91e26a5ec88cd4eac70223b62bd03`, 688 bytes)
    - `materials/attachments/kernel.config` ← `work/materials/pwn-v11/saj-2021-pwn-ebpf/public/kernel.config` (`fa727b053326f4df70740bc86597c01a5ed717f90e10e024ebdab7a5d8079abc`, 127783 bytes)
    - `materials/attachments/musl_bpf.h` ← `work/materials/pwn-v11/saj-2021-pwn-ebpf/public/musl_bpf.h` (`0e6e2926833269e54794c253b5f89987e95a84b39bdcf72e852c659df0db938e`, 13212 bytes)
    - `materials/attachments/root.cpio` ← `work/materials/pwn-v11/saj-2021-pwn-ebpf/public/root.cpio` (`b2637596852173ca5b633c21a449c69d2f57042705cef884152e7a0494792564`, 5029888 bytes)
    - `materials/attachments/verifier.c.patch` ← `work/materials/pwn-v11/saj-2021-pwn-ebpf/public/verifier.c.patch` (`019789673e60ba570bef084533e1c4c1705de50b71209a0699edf517b4a87730`, 1930 bytes)
  - W: absent
  - P (4):
    - `materials/exploit/exp.c` ← `work/materials/pwn-v11/saj-2021-pwn-ebpf/solve/exp.c` (`1b8f31f0ed1d30c0017b365a4575a432f4de457b024b7d55d9ad6fbbe06ce096`, 12754 bytes)
    - `materials/exploit/exp.ed0c59da.py` ← `work/materials/pwn-v11/saj-2021-pwn-ebpf/solve/exp.ed0c59da.py` (`489bd7b848a6e43ee3813ff5a96b58f99338a4cfa9ba5ab674d4e56d1b45b86a`, 877 bytes)
    - `materials/exploit/exp.py` ← `work/materials/pwn-v11/saj-2021-pwn-ebpf/solve/exp.py` (`0291dc7f339ab280c789ac2b13316a9b4d6bceb57e5d33251ee2df8b8cb5394e`, 3504 bytes)
    - `materials/exploit/exp/exploit.c` ← `work/materials/pwn-v11/saj-2021-pwn-ebpf/solve/exp/exploit.c` (`3669af81660cdf9436025aa032669ca48cc9f40ac56b6ed68b7baf9da176d36d`, 3813 bytes)
  - B (2):
    - `materials/deployment/exp/Makefile` ← `work/materials/pwn-v11/saj-2021-pwn-ebpf/build/exp/Makefile` (`729a9455b94cfb07fd76c96db0d5747bf0b213eb55969c9f8c5bab035d8c017a`, 107 bytes)
    - `materials/deployment/start.sh` ← `work/materials/pwn-v11/saj-2021-pwn-ebpf/build/start.sh` (`d10977a7006e2af173ae8b5065c045a1f09f0267aab5b04ad33324c71cf68eb4`, 807 bytes)

### 13. `saj-2022-pwn-babyheap2022` — babyheap2022

- Identity: 0CTF / 2022 / Pwn
- Source: `0ops/ctfs`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/0CTF/2022/pwn/babyheap2022`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `prebuilt_rehost`; `system_libc`; `heap`, `shellcode_seccomp`, `stack_rop`
- Selection reason: fills build_mode:prebuilt_rehost; fills complexity:small; fills runtime:system_libc; fills year_bucket:2022; adds event 0CTF; adds source 0ops/ctfs
- Material fingerprint: `d117995be3e09b546d61461aef0df277bd1f40111d8a61edee820eabf5df9627`
- Material paths:
  - A (15):
    - `materials/attachments/address-of-guard.png` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/public/address-of-guard.png` (`76e97403bd8cf376dfdaae12a97c4b463cd970363b54662772b0cf4a2978d329`, 21968 bytes)
    - `materials/attachments/babyheap` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/public/babyheap` (`e0ed20b136d431f1abe687fb80a3280b9b583d0cc55945bc54a4b166ee1b0848`, 14464 bytes)
    - `materials/attachments/call-exit-function.png` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/public/call-exit-function.png` (`40f465b5957c68484e4f35a8200d821ccee3d5e534721d71f74bc73b2d8a560f`, 26579 bytes)
    - `materials/attachments/call-tls-dtors.png` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/public/call-tls-dtors.png` (`443d94ad08c3c6c6ebb1539552f2ca62afa612ddb7e15c689890f98d8eadbab9`, 8464 bytes)
    - `materials/attachments/challenge.json` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/public/challenge.json` (`88873c6dd756be8e0c269ca8512b6c3efd298b1c2216a3bda1e63733e0959744`, 1097 bytes)
    - `materials/attachments/check-offset.png` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/public/check-offset.png` (`8a456bd3bb89e91d3c99dcf4a8335c605495a3af9540bc87af39b88aedffc21b`, 4976 bytes)
    - `materials/attachments/execute-ropchain.png` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/public/execute-ropchain.png` (`0dbabb92981f81d4e8bc4acfba44e0573857e2314078a6b345f1f9019aeee30a`, 52702 bytes)
    - `materials/attachments/f-structure.png` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/public/f-structure.png` (`00d4828f41521ae8016058242a7b6cc0fd225ec173d69eb5fbd8f7c63c41c065`, 5116 bytes)
    - `materials/attachments/get-address-of-first-dtor-list.png` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/public/get-address-of-first-dtor-list.png` (`a2e1f5e1aaa00b8130e858548a5655646d1eec2dd0536b829be40d8a62b0ac4c`, 18307 bytes)
    - `materials/attachments/get-address-of-fs.png` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/public/get-address-of-fs.png` (`2d42dd72c8aba5966bf8e116b87bd6c7fb2cffac61ec1ea64d52030e7d44b514`, 64448 bytes)
    - `materials/attachments/get-address-of-tls-dtor-list.png` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/public/get-address-of-tls-dtor-list.png` (`5d0b35b5261a46ff4be98393c2049f14b6a3eefd3cd5b9f69f69fd115c980c8b`, 26109 bytes)
    - `materials/attachments/ropgadget-find-rdx-rsp.png` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/public/ropgadget-find-rdx-rsp.png` (`bd9ea931447b6f509736e8716525567736e82f1719f8694ab4320fa302fe4d3c`, 12431 bytes)
    - `materials/attachments/seccomp-setup.png` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/public/seccomp-setup.png` (`ef032b44215364c1950bc2fde9728bdfe2d4f04ec8872cee1aefd259c76e69d2`, 91454 bytes)
    - `materials/attachments/segfault-dtor-list.png` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/public/segfault-dtor-list.png` (`1dd14ee2298fa469ef80069c0a5f70c66730803f4108d37372fec45d88ac0d50`, 25356 bytes)
    - `materials/attachments/update.png` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/public/update.png` (`206da99c0481a75d624d57b2339d7eef824d8d95055004a2e5270b6a6e1c15c3`, 39160 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/writeups/README.md` (`03be1f3df19fcb50ae73299a2d4ccdc52b1e45b5df1aecbeb3e78108cac44863`, 16501 bytes)
  - P (3):
    - `materials/exploit/solve.9e799bbc.py` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/solve/solve.9e799bbc.py` (`676f77f41dddd25ed988dc1a7eacc0dea2dfe850039432ce2ebebdd328e24803`, 4611 bytes)
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/solve/solve.py` (`25179b2304ec1c6f3a6a3184aaccfb2239b81feccff1e8cd34478daa21fa3e15`, 3634 bytes)
    - `materials/exploit/solve/solve.py` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/solve/solve/solve.py` (`9baa3fb4a6cb22c7d2373bfca60fd69cafa85883f019eb04f36d64c250409792`, 6507 bytes)
  - B (3):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/build/Dockerfile` (`7dbd4e0764e0fc8600a8497be79ce54476a8b7dbedc5f3dfdff621f468b4d5d4`, 743 bytes)
    - `materials/deployment/Dockerfile.bd657f7e` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/build/Dockerfile.bd657f7e` (`6857656c81fdbae6a4aad8a00bde23fa6f691ae226125e23fe928e81c62d3e53`, 293 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/saj-2022-pwn-babyheap2022/build/docker-compose.yml` (`53326d56620de2543289801f77d2c2fbe92ccde63dcf7af8e06ab0885dc95158`, 181 bytes)

### 14. `gh-c1e81f2d4281418ac05aa50a` — handlers

- Identity: Hackfest / 2023 / Pwn
- Source: `M0ngi/CTF-Writeups`; `https://github.com/M0ngi/CTF-Writeups/tree/327864f1597112e9072dcbcfe0c8e5254c91dea9/2023/Hackfest Quals/pwn/handlers`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `prebuilt_rehost`; `bundled_libc_loader`; `other`
- Selection reason: fills build_mode:prebuilt_rehost; fills complexity:medium; fills runtime:bundled_libc_loader; fills year_bucket:2023; adds event Hackfest; adds source M0ngi/CTF-Writeups
- Material fingerprint: `b1c2b61870a6b12989e74581b6fcfcb79d3d311d2e6e80cbd4968e4561322596`
- Material paths:
  - A (4):
    - `materials/attachments/ld-linux-x86-64.so.2` ← `work/materials/pwn-v11/gh-c1e81f2d4281418ac05aa50a/public/ld-linux-x86-64.so.2` (`28042f71786188a819e9f25abc67130071f88dfd20cb0140401d9aea1eb8bea8`, 224376 bytes)
    - `materials/attachments/libc.so.6` ← `work/materials/pwn-v11/gh-c1e81f2d4281418ac05aa50a/public/libc.so.6` (`8f7b479e581eabe2dbbc3cbf0099a1d71252ca0a470aeafc57f22f0822257188`, 2072888 bytes)
    - `materials/attachments/main` ← `work/materials/pwn-v11/gh-c1e81f2d4281418ac05aa50a/public/main` (`c1a6f01cc8df7aa997f3f46465b88b47d49e02f8cffcc8bfbf4c8afdffe73066`, 17688 bytes)
    - `materials/attachments/main_original` ← `work/materials/pwn-v11/gh-c1e81f2d4281418ac05aa50a/public/main_original` (`d0845c368b1c9bbb5e559d34e86ebeb68e07a3adee7525c73ef5acbe3034b9ea`, 16376 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/gh-c1e81f2d4281418ac05aa50a/solve/solve.py` (`0a028b5c67a095d495c256dc6014fdcff505368ea6d385e624a626270c3695cf`, 3046 bytes)
  - B (1):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-c1e81f2d4281418ac05aa50a/build/Dockerfile` (`60320f2b748d81b72ddf48e43b8aaede4d5038d48926f7ee42ff52ce34ac7a28`, 179 bytes)

### 15. `gh-d9f263b7fbb551151920acd8` — babykernel

- Identity: hacklu / 2018 / Pwn
- Source: `sixstars/CTF`; `https://github.com/sixstars/ctf/tree/797933e5397b1e6ee7cc14982c478bec183d15bc/2018/hacklu/babykernel`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `build_metadata`; `hybrid`; `static`; `kernel`
- Selection reason: fills complexity:large; fills runtime:static; fills year_bucket:pre_2020; adds event hacklu; adds year 2018; adds source sixstars/CTF
- Material fingerprint: `c3284ad8000e2c8f2df1570e76b15e78bc870da6657d31a645c0aa9d3f0b20a2`
- Material paths:
  - A (17):
    - `materials/attachments/authorized_keys` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/public/authorized_keys` (`b8fa8b01c9f97b87166142a071789b0219e4f33a1faccd5e0372f6c6723fbc65`, 380 bytes)
    - `materials/attachments/baby_kernel_3460960b6fc99f8a90fba7397b5e4c46/public/bzImage` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/public/baby_kernel_3460960b6fc99f8a90fba7397b5e4c46/public/bzImage` (`ee26dc3efb885eab6ca47f49018bb0f1eadf9542438567256f131e497698de23`, 2179120 bytes)
    - `materials/attachments/baby_kernel_3460960b6fc99f8a90fba7397b5e4c46/public/initrd.cpio` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/public/baby_kernel_3460960b6fc99f8a90fba7397b5e4c46/public/initrd.cpio` (`c32a28498d5554e7411c56efdcae7d38585ff1072005c0ffcf446b1d38d1bb0d`, 7787008 bytes)
    - `materials/attachments/baby_kernel_3460960b6fc99f8a90fba7397b5e4c46/public/vmlinux` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/public/baby_kernel_3460960b6fc99f8a90fba7397b5e4c46/public/vmlinux` (`1271b21d868563e0e2dc9907e07177cf9ac86ec14c535971041c3fff6a6b046a`, 91609360 bytes)
    - `materials/attachments/busybox` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/public/busybox` (`a1ba337c04f32857fc4d80fd2c2e0074a673536df9a97f5e623c1a3266901115`, 2572544 bytes)
    - `materials/attachments/client_kernel_baby` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/public/client_kernel_baby` (`194844a95f692e54e8534b389620c6d600ddfda2d34c2eef8b7fa2d85aecd173`, 875096 bytes)
    - `materials/attachments/debug` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/public/debug` (`78887d09be6971d06c0cfc4c52d6df611cc06c04f2521d7b5252e2e39739377b`, 136 bytes)
    - `materials/attachments/group` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/public/group` (`1c955bc0cb6e000e53023ea46dc26d02cd9afe956a63d83e971c81326cb96c36`, 31 bytes)
    - `materials/attachments/hack.py` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/public/hack.py` (`7cd911a6e4082bb72472d9513ac1cba8223a61799a8c76e844e1f6661cff7fd5`, 990 bytes)
    - `materials/attachments/init` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/public/init` (`6bf5e15dc65cd581cc4df606cb056a0e2965f7b2d69a505e208afc5328771e65`, 1276 bytes)
    - `materials/attachments/inittab` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/public/inittab` (`842118cbdcf49ac530a832bd4d565baba9906738822f35b0a77cf81dd99d8d1e`, 39 bytes)
    - `materials/attachments/kernel_baby.ko` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/public/kernel_baby.ko` (`4a052d6cf434f68ed5cc9b3947da3dd344edbc9ee3f7852d08f9809e1998e9e8`, 209672 bytes)
    - `materials/attachments/main` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/public/main` (`3e24999d1c6525c05d729d640adb5368dc93b693f291643daf0e7074d1b8b02b`, 8720 bytes)
    - `materials/attachments/main.c` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/public/main.c` (`44409e71e0afcefefaded5c80bb2b4374595f16f98633b5f80169e7f50c3c9e0`, 277 bytes)
    - `materials/attachments/passwd` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/public/passwd` (`c688483f7b057cd10d0beda108e8bc272483954fce1d882b874a2b9a7e592024`, 71 bytes)
    - `materials/attachments/peda-session-unknown.txt` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/public/peda-session-unknown.txt` (`538d6440534fa5f615e8a26932792a82a2e4a33a97886e2d815eab8fc216d415`, 7 bytes)
    - `materials/attachments/shadow` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/public/shadow` (`c5403da1557dcf8635f1e7853f17c50faf6777e679d405345138cbe4837fe6dd`, 45 bytes)
  - W (2):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/writeups/README.md` (`a52fb7601482958e7d99d3cf05d9ca7a62ccb4b14cfbf32dc90fe5683e2eec35`, 32552 bytes)
    - `materials/writeups/readme.md` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/writeups/readme.md` (`5d7c13e51c8a141d52a4bc827904935a653557c1d0a6830ccddc36f85c6852fd`, 2279 bytes)
  - P (1):
    - `materials/exploit/exploit.py` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/solve/exploit.py` (`9a1fce39237f152bfcd42bd08798c7b1b5a36ff7ea43dd035e753f54c7e77247`, 433 bytes)
  - B (1):
    - `materials/deployment/run.sh` ← `work/materials/pwn-v11/gh-d9f263b7fbb551151920acd8/build/run.sh` (`5d0589b887d9ed9e67094cd083a74e3a427d3c328219d5cc7e91451d68246c69`, 130 bytes)

### 16. `saj-2023-pwn-enterprise-blockchain` — Enterprise_Blockchain

- Identity: Paradigm / 2023 / Pwn
- Source: `paradigmxyz/paradigm-ctf-2022`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/Paradigm/2023/pwn/Enterprise_Blockchain`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile_compose`; `source_build`; `unknown_or_non_elf`; `other`
- Selection reason: fills build_mode:source_build; fills complexity:large; fills topology:multi_service; fills year_bucket:2023; adds event Paradigm; adds source paradigmxyz/paradigm-ctf-2022
- Material fingerprint: `1e80b07669302b7796adf81b73234a6f066f77ef8d785bf8b1372cf856573dfa`
- Material paths:
  - A (27):
    - `materials/attachments/Bridge.sol` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/Bridge.sol` (`0864ad7c1cdaf9d0e51ff8b15dddf0d4b690f5c2f5d2dece3f1127b88ef78480`, 6321 bytes)
    - `materials/attachments/BridgedERC20.sol` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/BridgedERC20.sol` (`a084f1dc0b5cdba98075e18936117219740477465769ad853b8a9feba8beb689`, 1269 bytes)
    - `materials/attachments/CTFDeployment.sol` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/CTFDeployment.sol` (`df0b4c797be028f1860e9dee17d33b6e274a256dd253004a0abf73c047e983e4`, 1004 bytes)
    - `materials/attachments/CTFSolver.sol` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/CTFSolver.sol` (`d2dbc3105254ab588ef287dadbfbea13492e99b819d3c15b7d77af06d84f0eb3`, 571 bytes)
    - `materials/attachments/Challenge.sol` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/Challenge.sol` (`9c34153dc36dcd411ad2d7842e9717fab160797c199c92f0afbb4176c605232b`, 418 bytes)
    - `materials/attachments/Deploy.s.sol` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/Deploy.s.sol` (`feb796fe30e3cd67d307e45da45f17f1b461bba70fd8be06af2598f49d5877f7`, 1179 bytes)
    - `materials/attachments/IBridge.sol` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/IBridge.sol` (`b9bb3aa9337e527f8d5b0c83366187991252b2911c7589de8c82209c1e707d3f`, 212 bytes)
    - `materials/attachments/MultiSig.sol` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/MultiSig.sol` (`b6f22c3bb66c1d0a9e6bc4a5f37617f2e8efa36da867252cbe406097911b534d`, 1847 bytes)
    - `materials/attachments/README.md` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/README.md` (`ed87afce2b4ce88be7d7e40224086c0f783b7d3e479aa080f9c4e97162b7d28b`, 112 bytes)
    - `materials/attachments/challenge.e008d7ea.py` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/challenge.e008d7ea.py` (`6de468ae744353fe6c73de3aff87aafda1cbf70d98e41d4d6ba60338c951b812`, 2809 bytes)
    - `materials/attachments/challenge.py` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/challenge.py` (`2760059006483a6d03ea6b54313a429264376a4d602b328a5f69e731a97b47ae`, 2978 bytes)
    - `materials/attachments/exit-prerelease.sh` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/exit-prerelease.sh` (`6704ee5febfa5305297b59bbea4b7769723d49e9a22bec9ee1932400bfe88b20`, 131 bytes)
    - `materials/attachments/format-changelog.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/format-changelog.js` (`e98c4c231803fb239db92fef68e6191349379c73751e015909c2b384a0754d08`, 1227 bytes)
    - `materials/attachments/foundry.patch` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/foundry.patch` (`728107fc4462a3f18e6b4c4a45c4fd9a88a511e406e402c5d7f755bc01c526fe`, 1962 bytes)
    - `materials/attachments/github-release.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/github-release.js` (`4b88436e2c81e284ee0875402f21f63bb693ae3da96eac6d18d6cfdefb4217b4`, 1660 bytes)
    - `materials/attachments/integrity-check.sh` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/integrity-check.sh` (`8273d50ed3cc000ef734fbeecead6c35e46912614d5ff1bb1ec8174c37725494`, 439 bytes)
    - `materials/attachments/pack.sh` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/pack.sh` (`38f787a8c9e2c38bd92208bf33cae0928867d0c2441d07a74cb1a0d5da248b63`, 705 bytes)
    - `materials/attachments/publish.sh` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/publish.sh` (`694d3b89c294caf10d3e7a030c84bd44027764dd1833d691875547390e9d4a4f`, 763 bytes)
    - `materials/attachments/relayer.cc83e68e.py` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/relayer.cc83e68e.py` (`e4d10fbdb8714b08f62f17e79766d909cb88b37ab3a2d8507f5203f685285838`, 4988 bytes)
    - `materials/attachments/relayer.py` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/relayer.py` (`bc91f6be2c1f51ffd2adf94e91f31f019313ca9c2da54b3761451f4d2a08eb9a`, 4976 bytes)
    - `materials/attachments/rerun.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/rerun.js` (`e6463d98a64df5794190341fe03aa3123dbac1d7ac46160b95bed3daa038aa0c`, 250 bytes)
    - `materials/attachments/revm.patch` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/revm.patch` (`66c8daa981f9ae92fef1337c74088747d04a8d1efde742884e9850efdcd08d44`, 14525 bytes)
    - `materials/attachments/set-changesets-pr-title.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/set-changesets-pr-title.js` (`05305204f28f947b74ffa055756958d8ed7589ef5ded1b7fe711d1e463064747`, 768 bytes)
    - `materials/attachments/state.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/state.js` (`d118f68312375d260a438ebf70d01979fae780d35853b66bd873b72ee780979d`, 3587 bytes)
    - `materials/attachments/synchronize-versions.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/synchronize-versions.js` (`477c2b3c846a9faf36afa1a66d3ed8a7008a80aaec5a096ee7ed4d6a3ac1d54a`, 481 bytes)
    - `materials/attachments/update-comment.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/update-comment.js` (`258bad59128bf2f39480fc719a0d8b4b5874d84a877ca00953854f66ce3ef48d`, 1280 bytes)
    - `materials/attachments/version.sh` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/public/version.sh` (`0370ba51bb00887c2a679e7094f9adf5813ad9d3de7c48822750cfd28bc954d4`, 193 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/challenge/solve.py` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/solve/challenge/solve.py` (`d240dc4d321d8fd6f2d3e1c206841a41ad25a481fad0e9938c8e5ca9dd9dd27d`, 3953 bytes)
  - B (180):
    - `materials/deployment/challenge/Dockerfile` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/Dockerfile` (`b1118362341573b7b53fcb8fba67001c21b02f96438fe57f92e11a2bdc6af05e`, 906 bytes)
    - `materials/deployment/challenge/challenge.py` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/challenge.py` (`2760059006483a6d03ea6b54313a429264376a4d602b328a5f69e731a97b47ae`, 2978 bytes)
    - `materials/deployment/challenge/docker-compose.yml` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/docker-compose.yml` (`8bb4fcd82d6a8ca4ce728c2c76b743f2f235bbcd667ba702ca7b4cae935d170d`, 826 bytes)
    - `materials/deployment/challenge/foundry/Dockerfile` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/foundry/Dockerfile` (`086df95c4e481dcbcfeb568da293882c648877c9436230ef51f0820809632b7e`, 692 bytes)
    - `materials/deployment/challenge/project/lib/forge-std/lib/ds-test/Makefile` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/forge-std/lib/ds-test/Makefile` (`1635325116250a7b15916fc561f70664be3a267efcc582257f7903ba80e43e1a`, 277 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/.mocharc.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/.mocharc.js` (`434e1df653523a6bce5e53a62690018b51039b10fab4a734a10948bedd06789d`, 70 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/.solcover.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/.solcover.js` (`718b6563375d9c6701269414b19eafde40f4ab18bd0fbd8f9aaf6137141febb5`, 275 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/certora/Makefile` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/certora/Makefile` (`102cfe97d0dde7b6f6d7c29df98ad44e57c0ac46944832f9299ee956be682660`, 1695 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/certora/run.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/certora/run.js` (`d2d11e62fd6e5cefbc43ebcf535ca140616e7fab85ce4c69d915dacd0495e691`, 4107 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/docs/config.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/docs/config.js` (`d5cdaf3c2d7b2724173f9664210cfae1aa4a700bf2a1f6a7b7820b74b04c15e7`, 748 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/docs/templates/helpers.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/docs/templates/helpers.js` (`c54072a039eb8e30ebdfc050e2366c4fd2d33aaef32693e000b355c28899fa13`, 1423 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/docs/templates/properties.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/docs/templates/properties.js` (`0d1a82b32b77dec629c2bd122fce327fe8f4f75e6187b6b6049bc340d793dfb0`, 2081 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/hardhat.config.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/hardhat.config.js` (`85d6fedad19d95e76f779204e700814d4315a6bc996df9a184f136a86f7e0f18`, 3209 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/hardhat/env-artifacts.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/hardhat/env-artifacts.js` (`0afbe829adfa2d60c91b0c175beb97ab637b6d80ce7ddeaa3f10a19004c081a2`, 850 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/hardhat/env-contract.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/hardhat/env-contract.js` (`295452bfe42541c92fece832a81c2b98418476b6d4b2468da7f96bab6896308a`, 733 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/hardhat/ignore-unreachable-warnings.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/hardhat/ignore-unreachable-warnings.js` (`5881535d1f4d05527a4481c6f0cd85156309e1623692b0d6a54139da67af96a3`, 2018 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/hardhat/skip-foundry-tests.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/hardhat/skip-foundry-tests.js` (`5e594373be07d38818abb95c62e159435c68e291aa230e7d95fc2e38f00cb8ea`, 295 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/hardhat/task-test-get-files.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/hardhat/task-test-get-files.js` (`9851350b493983460df169f1c5dedac9c36930ee5bdbddaf977fb5fa75925a86`, 1008 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/checks/compare-layout.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/checks/compare-layout.js` (`50d63869428eff743ac96355892250e30dcff323303d3c16a067a6f57d952ddf`, 662 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/checks/compareGasReports.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/checks/compareGasReports.js` (`c47be4fdb00d7ea3243fe4397208d42fb2f6eef639e218e2078e4b26fa42824a`, 6853 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/checks/extract-layout.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/checks/extract-layout.js` (`2c94e7b5cb32f542c6e4a7dd137a0d567114fa604d447d800013bed1b680ccb0`, 1122 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/checks/generation.sh` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/checks/generation.sh` (`8880f5955713670cd62ee7ef7440f57cc71cab477b654910cdbed95cf0f35562`, 81 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/checks/inheritance-ordering.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/checks/inheritance-ordering.js` (`b3f0fa6fd440d2b953a929d01f50b5ea3c13040143f402a8c396925861bc2ade`, 1949 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/gen-nav.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/gen-nav.js` (`4705c4cecad88a47dbb0dc8f1d854d17669b74851d57c16d6130cc6ebcf73af8`, 984 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/generate/format-lines.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/generate/format-lines.js` (`de8e8ae2542d2db777ff3441efdd1b3f549c5ba473f1071180451c5e25575c12`, 422 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/generate/run.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/generate/run.js` (`c101b1e537b5708dc2c2591684a99b9df380e5e9bbe12fea1c90fee35b5382a7`, 1561 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/generate/templates/Checkpoints.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/generate/templates/Checkpoints.js` (`5d871ee96231baf1dd046ddba83a9580f5bf5ad975886e3142aa480c3f6d709d`, 8337 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/generate/templates/Checkpoints.opts.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/generate/templates/Checkpoints.opts.js` (`47ac1d11a3e082049539e930b28e179cb665ce2c04e64bb434a606a591accaba`, 411 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/generate/templates/Checkpoints.t.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/generate/templates/Checkpoints.t.js` (`82d6bd91baaf8cc2f917045dc3a91f84027dfcefb1b2bfff02b5a32972743bcc`, 4532 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/generate/templates/EnumerableMap.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/generate/templates/EnumerableMap.js` (`aefaf222e29dd026e12ad88340a0edc9c46d7d71692735f15eab541436f792bd`, 9018 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/generate/templates/EnumerableSet.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/generate/templates/EnumerableSet.js` (`974a160be25ca121b4d82fbc0c345ced74ed4b6e8b5af50f501e486538ad988e`, 7870 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/generate/templates/SafeCast.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/generate/templates/SafeCast.js` (`249cdd3f1ecbd9c555711630842a2d1c4c2a6e31f034cf8953fb3b622c8080eb`, 3573 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/generate/templates/StorageSlot.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/generate/templates/StorageSlot.js` (`4251526aa4b087db5f0f9d51186dc98296e636e3ecc5e9c189791e899a2136fa`, 2447 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/generate/templates/conversion.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/generate/templates/conversion.js` (`134a41ead4e00cff47ef7d0f99b68dea2e730f5a8cc02dbca22f7603fb5b10f8`, 678 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/git-user-config.sh` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/git-user-config.sh` (`12aebe7237d64a19e85521626ed5e868e14110c0b8aa8c966e44292380489685`, 159 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/helpers.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/helpers.js` (`9fbf5211b019430e2180e53568e5a9d49a70ebf1a55e0a83e55709338c8967d0`, 812 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/prepack.sh` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/prepack.sh` (`9d45771e720916935175b354c3c48877cb0cb43e7c262e544d2bf5c7728baee4`, 478 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/prepare-docs.sh` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/prepare-docs.sh` (`438539860f7263c460df17a18fba4de876fcc109fff76639ad86a463474d0c9f`, 622 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/release/format-changelog.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/release/format-changelog.js` (`e98c4c231803fb239db92fef68e6191349379c73751e015909c2b384a0754d08`, 1227 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/release/synchronize-versions.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/release/synchronize-versions.js` (`477c2b3c846a9faf36afa1a66d3ed8a7008a80aaec5a096ee7ed4d6a3ac1d54a`, 481 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/release/update-comment.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/release/update-comment.js` (`258bad59128bf2f39480fc719a0d8b4b5874d84a877ca00953854f66ce3ef48d`, 1280 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/release/version.sh` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/release/version.sh` (`0370ba51bb00887c2a679e7094f9adf5813ad9d3de7c48822750cfd28bc954d4`, 193 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/release/workflow/exit-prerelease.sh` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/release/workflow/exit-prerelease.sh` (`6704ee5febfa5305297b59bbea4b7769723d49e9a22bec9ee1932400bfe88b20`, 131 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/release/workflow/github-release.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/release/workflow/github-release.js` (`4b88436e2c81e284ee0875402f21f63bb693ae3da96eac6d18d6cfdefb4217b4`, 1660 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/release/workflow/integrity-check.sh` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/release/workflow/integrity-check.sh` (`8273d50ed3cc000ef734fbeecead6c35e46912614d5ff1bb1ec8174c37725494`, 439 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/release/workflow/pack.sh` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/release/workflow/pack.sh` (`38f787a8c9e2c38bd92208bf33cae0928867d0c2441d07a74cb1a0d5da248b63`, 705 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/release/workflow/publish.sh` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/release/workflow/publish.sh` (`694d3b89c294caf10d3e7a030c84bd44027764dd1833d691875547390e9d4a4f`, 763 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/release/workflow/rerun.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/release/workflow/rerun.js` (`e6463d98a64df5794190341fe03aa3123dbac1d7ac46160b95bed3daa038aa0c`, 250 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/release/workflow/set-changesets-pr-title.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/release/workflow/set-changesets-pr-title.js` (`05305204f28f947b74ffa055756958d8ed7589ef5ded1b7fe711d1e463064747`, 768 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/release/workflow/start.sh` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/release/workflow/start.sh` (`e85038c8827c10ce05272fab531909ff5d2082805ea4bc747d663bca2793ba90`, 1120 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/release/workflow/state.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/release/workflow/state.js` (`d118f68312375d260a438ebf70d01979fae780d35853b66bd873b72ee780979d`, 3587 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/remove-ignored-artifacts.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/remove-ignored-artifacts.js` (`d760c8c71b7a6936b34c663402ec735f254d157830c6f2df3c1497b59b4ec806`, 1318 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/solhint-custom/index.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/solhint-custom/index.js` (`ec74c407ef34fcd219172a93948f1b1dd8e68b945883f188ed478877593a65a3`, 2652 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/update-docs-branch.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/update-docs-branch.js` (`8fdd058f08eb817bbf2e85565e8922cc4984a013909d8d4116006c147788f56d`, 2099 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/upgradeable/patch-apply.sh` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/upgradeable/patch-apply.sh` (`459382902df6cf8045105df03e4c52d36db28f35f1162d044ce23eec6fc6efc4`, 410 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/upgradeable/patch-save.sh` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/upgradeable/patch-save.sh` (`315d98f74d9a2877c28130f841b5d3466748c9e8d4b90f7842108cc2308e37bf`, 388 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/upgradeable/transpile-onto.sh` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/upgradeable/transpile-onto.sh` (`5e02419866ad447f5106c8c30ec0cdca55ad7dbc5c654d828a5597402ff32799`, 1308 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/scripts/upgradeable/transpile.sh` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/scripts/upgradeable/transpile.sh` (`5e939cfaa553dd6e7b4f50aa8bbb570e032c2d6fdcbf2bc13795035dbc3eecfe`, 1527 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/solhint.config.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/solhint.config.js` (`19249d8fb9f74d11317432377e77a458e682a594f0f3c1606263813c321eb521`, 495 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/access/AccessControl.behavior.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/access/AccessControl.behavior.js` (`31a36de3df02890d207b7a1eb2009495d87928e094525e2f83e942ad29fbc37c`, 38232 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/access/AccessControl.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/access/AccessControl.test.js` (`e4253283237a5d3037a55eb568cdd1bef36c99a412245ae7f62f22beefca3439`, 449 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/access/Ownable.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/access/Ownable.test.js` (`b3b0db7baf546f84350f9a7ede3fc269987e81fafc4459736e3bc4b1476d2816`, 2422 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/access/Ownable2Step.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/access/Ownable2Step.test.js` (`8d7e6a4968cbd819d315c012c672c38cbe7fded67de5189cc320ea0e07fcfbb7`, 3170 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/access/extensions/AccessControlDefaultAdminRules.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/access/extensions/AccessControlDefaultAdminRules.test.js` (`af62ee2db8ffffb9739e67951839f54492f798702ef6481c1adcd2c4577c295a`, 942 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/access/extensions/AccessControlEnumerable.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/access/extensions/AccessControlEnumerable.test.js` (`80f66c7f06ab469d3d749cd88d37fba32e50fcd9b7431f31651c1e944da2e112`, 594 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/access/manager/AccessManaged.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/access/manager/AccessManaged.test.js` (`db993dd8708cda4dc243c75d3b044f387f5b1296005a94868bbfedceb9dca820`, 5652 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/access/manager/AccessManager.behavior.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/access/manager/AccessManager.behavior.js` (`a02c53384a8c2d5bff7c947524995cde4b0ce17f5888272ac3888fd554ff1dc7`, 25106 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/access/manager/AccessManager.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/access/manager/AccessManager.test.js` (`52ca4bd2bfb68e7d8c7e94ad0a7c9f98ae03ba15b6a2ce8ddab2e329a3bbbe53`, 114153 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/access/manager/AuthorityUtils.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/access/manager/AuthorityUtils.test.js` (`7ec904a95666d1972fad6e38e289de3f0cc86efe84398200c821b82e5b5b1f54`, 2991 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/finance/VestingWallet.behavior.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/finance/VestingWallet.behavior.js` (`25023bb0464bd5455e5e326b5f3be1403fe46f6373d86bbcefa649c047636399`, 2102 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/finance/VestingWallet.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/finance/VestingWallet.test.js` (`8b33f4a6e70cb1971070bb6d17ce8c5eb0d7993060d38ac78c15256580133a1f`, 2657 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/governance/Governor.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/governance/Governor.test.js` (`9e086d674d3eb021e7ea8d86403634ba92902c11ce33fe781b2b1a07ee0763df`, 41355 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/governance/TimelockController.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/governance/TimelockController.test.js` (`ca2fa219b5168331c1c839741715e3b8a59b06c6a11aaa32d83c05aec463e539`, 45271 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/governance/extensions/GovernorERC721.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/governance/extensions/GovernorERC721.test.js` (`7d095683f97aa70058552ca5918d3815aebe6f8cf6e6e2115b4f7106ca2a7065`, 4748 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/governance/extensions/GovernorPreventLateQuorum.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/governance/extensions/GovernorPreventLateQuorum.test.js` (`8b8e83d8fed96f7e61f7df0a66f7ad18b58cae5c38ab9d632a0d90dfc3ad794c`, 8687 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/governance/extensions/GovernorStorage.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/governance/extensions/GovernorStorage.test.js` (`cf146590659fadd3e4234b3afc01565629e3aa640a8ed626d8324f43724e6e4b`, 6954 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/governance/extensions/GovernorTimelockAccess.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/governance/extensions/GovernorTimelockAccess.test.js` (`c5c01d09f8794cc53056c60619f519933454abb08d29d9c8d1b06a8d35b2ce85`, 34150 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/governance/extensions/GovernorTimelockCompound.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/governance/extensions/GovernorTimelockCompound.test.js` (`ebb0c788b8288526fb7522435f64307b902051a36dd118f9b910a75588f3f364`, 18412 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/governance/extensions/GovernorTimelockControl.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/governance/extensions/GovernorTimelockControl.test.js` (`23fc2c3c112a9626996ec3c622860c5622d20a55c193ea70cec2982f983cc7f0`, 21606 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/governance/extensions/GovernorVotesQuorumFraction.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/governance/extensions/GovernorVotesQuorumFraction.test.js` (`77db5e6f09eb411bc530df7ce4795765b781e1b51978e257ef95a46549338f15`, 6829 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/governance/extensions/GovernorWithParams.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/governance/extensions/GovernorWithParams.test.js` (`2cc69b6aee9e0a9f2324c42f99088401cb6912d75fd39e486eed0d2177777bd5`, 11161 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/governance/utils/EIP6372.behavior.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/governance/utils/EIP6372.behavior.js` (`1634a38a1715f3a64997aadda07c98f4b671abf3095febecd99a818a4e984bb8`, 751 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/governance/utils/Votes.behavior.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/governance/utils/Votes.behavior.js` (`662b6c7e9f10673d2a68dcfa4a15f31eaf23deeb32f80f401badae30a6223845`, 14846 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/governance/utils/Votes.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/governance/utils/Votes.test.js` (`0cf85469b85204a2c6af78710b12ebc217b8313186290d506619f6475ffac602`, 3805 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/helpers/access-manager.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/helpers/access-manager.js` (`7ca6ce61f8bc4579a30098451dbb52bf22dd3ad0947d65718d6136f6b5d5cbaf`, 1751 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/helpers/account.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/helpers/account.js` (`f361a757890516d080d3ab1fdcc167c7bf05beb5cefedc2eb94ee4527f869ee3`, 410 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/helpers/chainid.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/helpers/chainid.js` (`7389af2dc017c84a00d53ff8717aa57748ea5cfaae5d6298252c38065421ed38`, 226 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/helpers/constants.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/helpers/constants.js` (`8623efacaee8171cb6f8a9fc0aa6a09620972114c018d1ccecfe6e30eeed5748`, 185 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/helpers/create.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/helpers/create.js` (`33638378d6a1b9e88c9cee6853cd60c47fea25ecda039878741305849f2eca7c`, 592 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/helpers/customError.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/helpers/customError.js` (`da4738a26fb86d91b3a3fc27be9f304484ba76ff3a050626c371aa0b821b1c22`, 1620 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/helpers/eip712.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/helpers/eip712.js` (`0a60085db798a748066809b4b66d83d5ce1bfc5f9783d20370c70feab197644c`, 1726 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/helpers/enums.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/helpers/enums.js` (`e0ef94a466aae67a3ff57fa6d6a9c88468afaa5b7f87a703efbdf93e7dda3bad`, 418 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/helpers/erc1967.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/helpers/erc1967.js` (`68e3b09067cea3367a6583d6be5eba195b0fbb78f6d2a6f7b5f1a9806d109b6d`, 1281 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/helpers/governance.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/helpers/governance.js` (`f1b2f5aed876b8be47a598370bfa358e9b08d93eacdee566f3ef2b99e3299825`, 8111 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/helpers/iterate.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/helpers/iterate.js` (`c4d252ce98d8c8018d437d495d38e8f5ffbcc310a987e8d592061526aa685c2a`, 543 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/helpers/math.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/helpers/math.js` (`4b652f5128955f2e7fdc3dfd6d8c76df0c8de0db625d9e4b568aee8d229b99a1`, 574 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/helpers/methods.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/helpers/methods.js` (`41c3a71d789fa4a98a05605af96f7e19b740fa741335e34834ea852aa560c4fb`, 138 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/helpers/sign.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/helpers/sign.js` (`c796e6763f45d4df40049f6627c0dd4c4ed37ac8feee4241c6e01bb926b904c6`, 2398 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/helpers/time.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/helpers/time.js` (`33b99d8f602b3fbabf9cbaee128871e15b938404534c64c934bd8ba9c8953692`, 556 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/helpers/txpool.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/helpers/txpool.js` (`47fd204b78ac79365629096e122fe5f006b56b69d0e83666daaa7c0564cab444`, 1130 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/metatx/ERC2771Context.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/metatx/ERC2771Context.test.js` (`b9f7e22819b764444871146d35e367103b19016d2ae4f6efdab7e0b6481a005b`, 5060 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/metatx/ERC2771Forwarder.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/metatx/ERC2771Forwarder.test.js` (`a109172d6d28fdd1aa5184c17c4672a899fdfb29dd5973b0d0f8121d713c0f3b`, 22648 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/proxy/Clones.behaviour.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/proxy/Clones.behaviour.js` (`09e88696ef3a7dffcac106720d0a016762037a5739fce0ca146fde3cfb8b412b`, 4507 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/proxy/Clones.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/proxy/Clones.test.js` (`b8718c51d7f1b3966f03de8710695109f7f9d8d07aa2d829116aac32be91428a`, 2621 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/proxy/ERC1967/ERC1967Proxy.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/proxy/ERC1967/ERC1967Proxy.test.js` (`4a991d8a87e433157ae3ef1dd4a5f6e7a2ec8e6330baec595936590498789371`, 451 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/proxy/ERC1967/ERC1967Utils.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/proxy/ERC1967/ERC1967Utils.test.js` (`0f22d7cd43d9fd2bb44dc1de9ae1e95f810c342a9142939f45e9bc62a8397c3d`, 7135 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/proxy/Proxy.behaviour.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/proxy/Proxy.behaviour.js` (`3ea705ec8ad4ece4c720d274de10f95312fe797b13ef62779319729e9fb69f9c`, 6244 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/proxy/beacon/BeaconProxy.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/proxy/beacon/BeaconProxy.test.js` (`57941f50337f127b2a2482287cfddb997d86729a6a6c6dfd5b0e95e7cde88ff5`, 5977 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/proxy/beacon/UpgradeableBeacon.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/proxy/beacon/UpgradeableBeacon.test.js` (`0d2ba9207af443726cff736d856be9018d3e2f39fac9865cce35d818e811d36e`, 2154 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/proxy/transparent/ProxyAdmin.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/proxy/transparent/ProxyAdmin.test.js` (`df0083a4133f71b350469fd9d4c4a086af2889f570a0b12e32db86faa311bfb7`, 4157 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/proxy/transparent/TransparentUpgradeableProxy.behaviour.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/proxy/transparent/TransparentUpgradeableProxy.behaviour.js` (`a34a72b23b58c2a27a1606a10fcf94b3fff1be9d5c908f0aa631c21da3880936`, 17122 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/proxy/transparent/TransparentUpgradeableProxy.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/proxy/transparent/TransparentUpgradeableProxy.test.js` (`431caea27d715e9aa812706912bd14b7eccd259b89f6b7dbb8bf1875f252ac8d`, 1019 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/proxy/utils/Initializable.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/proxy/utils/Initializable.test.js` (`7aafb27ecf7aa5117ffc99e5a8ab37e03c94028f9e5bcbeed22c5c6946dc09d0`, 9102 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/proxy/utils/UUPSUpgradeable.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/proxy/utils/UUPSUpgradeable.test.js` (`9a7eaadae18ca770b9475915acffd2b573e9f5c3d69db8f15187617c66ef8b2c`, 5696 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC1155/ERC1155.behavior.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC1155/ERC1155.behavior.js` (`0cc4ef2f21e106a68f0733060f39d1df94cc1a43e9ef7b8ee3a0df044792aafb`, 32524 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC1155/ERC1155.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC1155/ERC1155.test.js` (`306ed32943100d2c736cc163776846f4597ec77512f575c9b52915184c47418d`, 8952 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC1155/extensions/ERC1155Burnable.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC1155/extensions/ERC1155Burnable.test.js` (`6dba6258b4afca379287036d81503607d3e32c54fc8f5c6b8654764fdf410d99`, 2775 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC1155/extensions/ERC1155Pausable.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC1155/extensions/ERC1155Pausable.test.js` (`c03002fecbb13ab44ad571a4e38225ed1b2b11f71ab0a654eaab39d34c17340a`, 3763 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC1155/extensions/ERC1155Supply.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC1155/extensions/ERC1155Supply.test.js` (`879b33c684149b0f77b7614811dca33933d7a7dc6513a5ba94bef816c7ddcb7e`, 4399 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC1155/extensions/ERC1155URIStorage.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC1155/extensions/ERC1155URIStorage.test.js` (`0a19967cc8b47c341058d31c2c181812b61596804b5b8c7cad00c1a078ed5982`, 2282 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC1155/utils/ERC1155Holder.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC1155/utils/ERC1155Holder.test.js` (`47830474f6a93baa0d448fc9656c35461fbe2d949777984a5c9fcc76f3159e36`, 2119 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/ERC20.behavior.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/ERC20.behavior.js` (`9a01c3f6320705b03a8b581f7b6d8a15822c0267adaffe76ef09d5e89f57ee7c`, 12022 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/ERC20.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/ERC20.test.js` (`9efee2a5deabab43ca7894f132d10512f08cdd1911c8b4259f00d9db891145f1`, 7715 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC20Burnable.behavior.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC20Burnable.behavior.js` (`cfc10269e484e97ed5fdee3e636dff2cce8817ccd98e5d78f21af2817ef98677`, 3710 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC20Burnable.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC20Burnable.test.js` (`a9048f0944355c10ab96a25974c5aceae2ff9cd9f4a8997df43359e0e5d4f4f1`, 622 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC20Capped.behavior.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC20Capped.behavior.js` (`fc8ad76873ab1a42b7b4a24345d3da5efac9e301b9d074e28e35331a0e50057c`, 1095 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC20Capped.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC20Capped.test.js` (`0c1c71a6cf300f94459dfa7a07b4bf2aeac0bdec82d4ad8d0c4c192528297358`, 757 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC20FlashMint.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC20FlashMint.test.js` (`6099d270116d9d066b8e0376ad5972c4e2b35215bb72b3bb1a2e3c58e984ee91`, 8752 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC20Pausable.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC20Pausable.test.js` (`82efe2f98bf16c77172fd3b19fa235e6c3386fefc5669bc6b40b98e4ae8e440e`, 4685 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC20Permit.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC20Permit.test.js` (`2c4686f1d96b685bb1f45d8d21fd2276f6c4cb8e2846a7297b1fff4efab7e3ef`, 4051 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC20Votes.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC20Votes.test.js` (`dcf70c4ea37f93df4a02f29e0e67ae7301b7c229e73e33edb55b491eb20e8c3d`, 27196 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC20Wrapper.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC20Wrapper.test.js` (`ebf64fe93e1972860c66d410cb7f7a2f74e14eee162ac4aa0ee2f888023ad099`, 7647 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC4626.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/extensions/ERC4626.test.js` (`cc09cf204623474e4891bca9358b4679e04b176227c95b8caf1ec728290d8305`, 45791 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/utils/SafeERC20.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC20/utils/SafeERC20.test.js` (`c29f2bdd5c47a72b8e48d4fc36c48c7b91aa9af1d06f46e789599ec3b4f80e3b`, 8939 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/ERC721.behavior.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/ERC721.behavior.js` (`cd4e1a1d2979db2ba6a648caf3cee6d9af06664fdcc446060d012185b384dbc1`, 37820 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/ERC721.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/ERC721.test.js` (`a6200e571517bb4b7e25af142fe3036e03f45472af643ab6a11828124dbd2181`, 440 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/ERC721Enumerable.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/ERC721Enumerable.test.js` (`fd7d41ef86c81e8ffa426ecb1923cdb7f2e56c602542aac48859be54bb42e857`, 570 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/extensions/ERC721Burnable.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/extensions/ERC721Burnable.test.js` (`6d4a786f85724719e27a4c93d410f33a7e691882d111febc2bc001907d915e54`, 2758 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/extensions/ERC721Consecutive.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/extensions/ERC721Consecutive.test.js` (`5bd61b27f35d9b3e7edde3e05799b9d3e4b4137e8dfe91ee758f06f765237d1b`, 8107 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/extensions/ERC721Pausable.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/extensions/ERC721Pausable.test.js` (`159f68c6ffb85e04e164770de89ad5c8b591fdd6fae29e27a2fecc28c58b00b4`, 2948 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/extensions/ERC721Royalty.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/extensions/ERC721Royalty.test.js` (`81ce5551158d34ceb79feb0a2d654b8111789cff8b4c62fbaaf750749f6a8d98`, 1622 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/extensions/ERC721URIStorage.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/extensions/ERC721URIStorage.test.js` (`940b8c476926c3aafd65e5da0040d1af4063a05f8e5a174d1cf9065211eb0876`, 4208 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/extensions/ERC721Votes.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/extensions/ERC721Votes.test.js` (`c6e24c9206146f9b149cbf42637e3c97b103269800c329e86a0fdde013cb37be`, 8406 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/extensions/ERC721Wrapper.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/extensions/ERC721Wrapper.test.js` (`4958b445f3a84efbd747b467c72500a6babe36700064573693826ea6f7de3b87`, 10293 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/utils/ERC721Holder.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/ERC721/utils/ERC721Holder.test.js` (`7624dcf4148800492c482ca223202063a40517777dde4f7da236e87863d519fe`, 675 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/token/common/ERC2981.behavior.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/token/common/ERC2981.behavior.js` (`a07e426deaf7ede72fc521d74bb94452132fc339df92d897f7473b3ac83e4c41`, 6990 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/Address.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/Address.test.js` (`47d65cac57fc6ada5a759356efed49008a7ef9d8902ff976b73c2123053f3515`, 12837 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/Arrays.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/Arrays.test.js` (`ab92df793b757fae1fb0c693c5e625bfce0ec38313578450edb80c0bcd616eaf`, 4190 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/Base64.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/Base64.test.js` (`5ace68abcabbe655c03d57fb55f954d326a07cf8167f1f1c14495e5e6034a246`, 1122 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/Context.behavior.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/Context.behavior.js` (`59192ea9d1a19876ce853686a75f7c4d089cfb8570d23e7a7c0b5ef88d3f2b5c`, 1625 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/Context.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/Context.test.js` (`634c9afa64d2530b87be164964769e1c966b77808d285db1dbdd18a47bb9a9cf`, 487 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/Create2.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/Create2.test.js` (`f1e468a9f9e05bf834b1cb096d2c821a830459d410cb128886ce300dc87ad562`, 4375 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/Multicall.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/Multicall.test.js` (`a72529e7746e85dd366123188cbbc92d0882b80cb4a50075e56add57d26d5ba2`, 2797 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/Nonces.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/Nonces.test.js` (`a1e1680fd1cceaf976a0b93293ff1c4e65e8d7f322fb5dc06aa735f69ed17310`, 2461 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/Pausable.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/Pausable.test.js` (`c2d142d1069f714dfceb9f10b33ba08c9b387a8ed5827e5f29d716f52d776888`, 3057 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/ReentrancyGuard.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/ReentrancyGuard.test.js` (`9c8936289f7dd04d2921c94adedcbae29f4a7d7e4016b5919ae962e648de4fd4`, 1813 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/ShortStrings.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/ShortStrings.test.js` (`e19fb6584daa05440fbc75f5448704cfd0635b0077e9bcf4e76ef7ecd2334019`, 1890 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/StorageSlot.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/StorageSlot.test.js` (`b5d3bf1ed3eeb7df09a96fbb7821d67ac605f55742ef9d74fe829f7a97102595`, 5967 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/Strings.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/Strings.test.js` (`a00048b09c60f8d0012bfc37a3f550f58fd95981490ffeab6a8e2d3f5ddfd393`, 5452 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/cryptography/ECDSA.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/cryptography/ECDSA.test.js` (`d34da15cb56185d0cd126368e007cda705123e94f315c35ed8fb81e54a5a1415`, 9453 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/cryptography/EIP712.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/cryptography/EIP712.test.js` (`8c860250c0e21d752f6a695e36d889a448ea5580ebc31d1bc05a7fd418c021b0`, 3910 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/cryptography/MerkleProof.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/cryptography/MerkleProof.test.js` (`7a76727b1ffb36b6e07821715f1081b90611273d9de10697fabd9b897ed0cb59`, 8704 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/cryptography/MessageHashUtils.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/cryptography/MessageHashUtils.test.js` (`f45223622c6d0c84f48ee5b85159b9771142921d5bb7e2493395fc10d569bbe5`, 2086 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/cryptography/SignatureChecker.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/cryptography/SignatureChecker.test.js` (`39faa1f5a45b30e0588310787e12a17e23a9eaeb0f448438222ecefedb68b24b`, 2945 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/introspection/ERC165.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/introspection/ERC165.test.js` (`3c85f6f5ca24420308496db5932826b980b176c066d42147d33dd9f2fc2018ed`, 276 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/introspection/ERC165Checker.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/introspection/ERC165Checker.test.js` (`122657c93996e5e76ec57a822b064cc70e89ea16e155a73caa58e1dac77662f3`, 12643 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/introspection/SupportsInterface.behavior.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/introspection/SupportsInterface.behavior.js` (`3107355f7479ec9b0fe4b6808abcbcc2bca3b6a17aa837f27b3033423d6fbdca`, 5100 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/math/Math.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/math/Math.test.js` (`2c88afb0f617e4626eeb4a96eb2a018469324af6e8b61f4ff97ee2e74af843ab`, 20437 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/math/SafeCast.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/math/SafeCast.test.js` (`6ba2cfd5ee1d2ad19a2f11734e544e3e99390daac403bf041aec0cf6fa09e86b`, 5814 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/math/SignedMath.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/math/SignedMath.test.js` (`b620fb8ae26f18f0e2b3e34c7e3fe68a41ab66b4343fc3ca016a39dd3c5ba7d2`, 2497 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/structs/BitMap.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/structs/BitMap.test.js` (`15e03ca2087ae5b613845d1be68ebdad3f4c0dc2e2db6be07c358a71f271ead5`, 5187 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/structs/Checkpoints.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/structs/Checkpoints.test.js` (`916076bc6da65be43781ce25028223f1e9be27b3630cd41e6d8c61c6b2a9454d`, 6627 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/structs/DoubleEndedQueue.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/structs/DoubleEndedQueue.test.js` (`f8594473ef53b968a43aafc92e7e4e6853ae95f9ac21558b4976a9d23bf2a509`, 3587 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/structs/EnumerableMap.behavior.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/structs/EnumerableMap.behavior.js` (`2a75406c72c495ef70d5d4ee3a4c29c9ffe480987af0c247a07091a1a65e487e`, 5812 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/structs/EnumerableMap.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/structs/EnumerableMap.test.js` (`c45916faef1d68625a9eff88dca4ea41515e8c75c5e0d8048f8d8c04d20f7a9a`, 5475 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/structs/EnumerableSet.behavior.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/structs/EnumerableSet.behavior.js` (`4df504c8e49437e622cfe3e8916cc359a4febde98f3462c6981624b132397ec6`, 3915 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/structs/EnumerableSet.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/structs/EnumerableSet.test.js` (`85aaab2a4259981a45ed1ef4264ea590ae8a3db57ea5fb9ac1f59174eea37e7c`, 2507 bytes)
    - `materials/deployment/challenge/project/lib/openzeppelin-contracts/test/utils/types/Time.test.js` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/project/lib/openzeppelin-contracts/test/utils/types/Time.test.js` (`7e83a68e9bcd2f0cb06cbbd935fe29639e8bb3482eed9bb9a50776d34eabd465`, 4906 bytes)
    - `materials/deployment/challenge/relayer/Dockerfile` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/relayer/Dockerfile` (`719f7d313bffaeb8c36bb8a451e655e2d33f5faed2ec84f81f75ff825003d62d`, 147 bytes)
    - `materials/deployment/challenge/relayer/relayer.py` ← `work/materials/pwn-v11/saj-2023-pwn-enterprise-blockchain/build/challenge/relayer/relayer.py` (`bc91f6be2c1f51ffd2adf94e91f31f019313ca9c2da54b3761451f4d2a08eb9a`, 4976 bytes)

### 17. `saj-2022-pwn-krce` — krce

- Identity: zer0pts / 2022 / Pwn
- Source: `zer0pts/zer0pts-CTF-2022-Public`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/zer0pts/2022/pwn/krce`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `build_metadata`; `hybrid`; `system_libc`; `heap`, `kernel`, `stack_rop`, `vm_emulator`
- Selection reason: fills complexity:medium; fills year_bucket:2022; adds event zer0pts; adds source zer0pts/zer0pts-CTF-2022-Public
- Material fingerprint: `d69428a3ce71df1f91aa752f444cda72ab2dffe10821f59d727858da1465a22c`
- Material paths:
  - A (9):
    - `materials/attachments/buffer.c` ← `work/materials/pwn-v11/saj-2022-pwn-krce/public/buffer.c` (`acab64ab0cb4f103ac748ddf11e39839f19cbdef361adffa58cecf475b269147`, 2641 bytes)
    - `materials/attachments/buffer.ko` ← `work/materials/pwn-v11/saj-2022-pwn-krce/public/buffer.ko` (`34dc53c1a52a8dd59787f3bb2f9bbb1f189ebd104a2ca924fb1c18cab1f56d71`, 6808 bytes)
    - `materials/attachments/bzImage` ← `work/materials/pwn-v11/saj-2022-pwn-krce/public/bzImage` (`3f8eaa465af840aa22860f546273716365bc3718b6e849fb49f5e4df05487fd2`, 4871168 bytes)
    - `materials/attachments/interface` ← `work/materials/pwn-v11/saj-2022-pwn-krce/public/interface` (`2e17a6703c87a9111e323f046d652f9e942fd4d3cdeed20dbe2949237ff929b6`, 16448 bytes)
    - `materials/attachments/interface.c` ← `work/materials/pwn-v11/saj-2022-pwn-krce/public/interface.c` (`038c23337a32e49cd9687fa179dee55312c218e1648c79e8c2f41ad168ae26d8`, 2656 bytes)
    - `materials/attachments/rootfs.cpio` ← `work/materials/pwn-v11/saj-2022-pwn-krce/public/rootfs.cpio` (`7f30f65f986709510683a902c6b6140ace3eb6b1bfc361d2091f60413eb4aa6c`, 2473472 bytes)
    - `materials/attachments/start-qemu.782f2522.sh` ← `work/materials/pwn-v11/saj-2022-pwn-krce/public/start-qemu.782f2522.sh` (`8bd14358f25e94e68498f498c428ce50437ea18d117d8e0769c69e05fa331234`, 804 bytes)
    - `materials/attachments/start-qemu.sh` ← `work/materials/pwn-v11/saj-2022-pwn-krce/public/start-qemu.sh` (`705ede12c768d2c1dea99d8bd498a5c3444a95565844fafd7f8dd08eaa3a23eb`, 285 bytes)
    - `materials/attachments/task.yml` ← `work/materials/pwn-v11/saj-2022-pwn-krce/public/task.yml` (`1a44fa6fce40dc5f16c8293711c8ec908c649e57e26d9275fad4296c20fde23d`, 236 bytes)
  - W (1):
    - `materials/writeups/local-community-wp-57dec395208fe94e3d374484.md` ← `work/materials/pwn-v11/saj-2022-pwn-krce/writeups/local-community-wp-57dec395208fe94e3d374484.md` (`6b9bb1e02db332b156e8c6db3d0d3dd62340e0bb8c2a00a3ed4af5c5baf37624`, 31705 bytes)
  - P (2):
    - `materials/exploit/exp.py` ← `work/materials/pwn-v11/saj-2022-pwn-krce/solve/exp.py` (`c54d29204671a2cc8bbbb0ceb9913d928af2662f6aa837257d02e05be56a6fb7`, 7427 bytes)
    - `materials/exploit/solution/solve.py` ← `work/materials/pwn-v11/saj-2022-pwn-krce/solve/solution/solve.py` (`53c46b97e49901f3ddfbc6218dbc66027534582547bc51a99da86f1c877725c2`, 3695 bytes)
  - B (1):
    - `materials/deployment/challenge/driver/Makefile` ← `work/materials/pwn-v11/saj-2022-pwn-krce/build/challenge/driver/Makefile` (`6798b19633e6693960c5bc7f442eb640f483361c35e835e47f05a74ec9f0daa1`, 351 bytes)

### 18. `saj-2025-pwn-debuggable-3` — debuggable_3

- Identity: smileyCTF / 2025 / Pwn
- Source: `ctf-gg/smileyctf-2025`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/smileyCTF/2025/pwn/debuggable_3`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `source_build`; `unknown_or_non_elf`; `format_string`, `heap`, `kernel`, `shellcode_seccomp`, `stack_rop`, `vm_emulator`
- Selection reason: fills complexity:small; fills year_bucket:2025_plus; adds event smileyCTF; adds source ctf-gg/smileyctf-2025
- Material fingerprint: `b91622e853976ea0cecbdaef9dd7670d6a6910cd133d53b691bacffe02b903a5`
- Material paths:
  - A (3):
    - `materials/attachments/challenge.toml` ← `work/materials/pwn-v11/saj-2025-pwn-debuggable-3/public/challenge.toml` (`05ae251c6ebd340a8878bf2756c2c2fed315eba4005d32aa080f3f55bb541b1d`, 405 bytes)
    - `materials/attachments/debuggable-3/run.py` ← `work/materials/pwn-v11/saj-2025-pwn-debuggable-3/public/debuggable-3/run.py` (`c7932cbc1cdd1fc131e1390ef5ca4051738779e5e8b7fe4d1acc5ab6cab98e07`, 537 bytes)
    - `materials/attachments/debuggable-3/script` ← `work/materials/pwn-v11/saj-2025-pwn-debuggable-3/public/debuggable-3/script` (`0d56b8a9b67e0ac1c9b1e41da339c0118cd17a8567e65ec4dca25be58b9f1667`, 22 bytes)
  - W: absent
  - P (2):
    - `materials/exploit/gef.py` ← `work/materials/pwn-v11/saj-2025-pwn-debuggable-3/solve/gef.py` (`0fc83d721057b3778af6b2d73d68a3065b1172ee0598759c63184b5867a77460`, 433584 bytes)
    - `materials/exploit/solve/solve.py` ← `work/materials/pwn-v11/saj-2025-pwn-debuggable-3/solve/solve/solve.py` (`a56fe4ed61296825d38bcf43b9211348a53a7e1c9419018258814cdd0d3d4cc6`, 156 bytes)
  - B (7):
    - `materials/deployment/dist/Dockerfile` ← `work/materials/pwn-v11/saj-2025-pwn-debuggable-3/build/dist/Dockerfile` (`26277b462021956d2e94b488278db015c49224104d438637901ee4179d24d4ae`, 453 bytes)
    - `materials/deployment/dist/run.py` ← `work/materials/pwn-v11/saj-2025-pwn-debuggable-3/build/dist/run.py` (`c7932cbc1cdd1fc131e1390ef5ca4051738779e5e8b7fe4d1acc5ab6cab98e07`, 537 bytes)
    - `materials/deployment/solve/build.sh` ← `work/materials/pwn-v11/saj-2025-pwn-debuggable-3/build/solve/build.sh` (`5eff89a9c4b50d2ff9520d54311c6bc0b15173dbc27fb38b4cf0778b30ecc6ef`, 198 bytes)
    - `materials/deployment/solve/fixup.py` ← `work/materials/pwn-v11/saj-2025-pwn-debuggable-3/build/solve/fixup.py` (`8099919ed6b29e689bfff51bb0bd633330e977a500d0af9192ceed826e3543e3`, 107 bytes)
    - `materials/deployment/solve/gef.py` ← `work/materials/pwn-v11/saj-2025-pwn-debuggable-3/build/solve/gef.py` (`0fc83d721057b3778af6b2d73d68a3065b1172ee0598759c63184b5867a77460`, 433584 bytes)
    - `materials/deployment/solve/main.c` ← `work/materials/pwn-v11/saj-2025-pwn-debuggable-3/build/solve/main.c` (`890196534d9abcff19b3bcd056cf98fa3dcca778ee80ec4e3232e743454da77a`, 26 bytes)
    - `materials/deployment/solve/test.c` ← `work/materials/pwn-v11/saj-2025-pwn-debuggable-3/build/solve/test.c` (`9a7f76717ee766624e20b069fbe496f9db7525029840262c60d7b893844cad10`, 45 bytes)

### 19. `gh-c328110b6995cac10415133f` — prng-service

- Identity: ekoparty pre ctf / 2015 / Pwn
- Source: `ByteBandits/writeups`; `https://github.com/ByteBandits/writeups/tree/559b5326f764bd9d9edc332e15ac41ae4f87d258/ekoparty-pre-ctf-2015/pwn/prng-service`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `build_metadata`; `source_build`; `unknown_or_non_elf`; `other`
- Selection reason: adds event ekoparty pre ctf; adds year 2015; adds source ByteBandits/writeups
- Material fingerprint: `a2fd5e98a499fdbbd0c4ac249420c39acef80c0c9835ee8f164b536101df56c4`
- Material paths:
  - A (3):
    - `materials/attachments/answer.h` ← `work/materials/pwn-v11/gh-c328110b6995cac10415133f/public/answer.h` (`968d8453e7cdf157e981139a0df3509a665cc54c038c3cb61288edf0fd1092e8`, 58 bytes)
    - `materials/attachments/pwn.py` ← `work/materials/pwn-v11/gh-c328110b6995cac10415133f/public/pwn.py` (`4841871c12e263904586287671046ba7c4aeee503934040faa550a42d43b2565`, 843 bytes)
    - `materials/attachments/pwn25.c` ← `work/materials/pwn-v11/gh-c328110b6995cac10415133f/public/pwn25.c` (`bc31f53a03426934683631e99da9e33cea8781d936688d22e341729b1b16fe17`, 1057 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/gh-c328110b6995cac10415133f/writeups/README.md` (`a27e70589ede27e484e97fbcb6ec3923efb363ae7702499f700dfe2c4422f1f2`, 2038 bytes)
  - P (1):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/gh-c328110b6995cac10415133f/solve/solve.py` (`98e8a410add4858be64657e104d148db7c1a1a939c6fc3dd8123b9c868f6353a`, 536 bytes)
  - B (1):
    - `materials/deployment/pwn25.c` ← `work/materials/pwn-v11/gh-c328110b6995cac10415133f/build/pwn25.c` (`bc31f53a03426934683631e99da9e33cea8781d936688d22e341729b1b16fe17`, 1057 bytes)

### 20. `gh-0f2902ebb6dd523a62b57f35` — 500 vm no fun

- Identity: SECCON online CTF / 2017 / Pwn
- Source: `SECCON/SECCON2017_online_CTF`; `https://github.com/SECCON/SECCON2017_online_CTF/tree/0a8bbd28544fbd89bed0f0e3eafa7b09a0165a6b/pwn/500_vm_no_fun`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `build_metadata`; `source_build`; `unknown_or_non_elf`; `other`
- Selection reason: adds event SECCON online CTF; adds year 2017; adds source SECCON/SECCON2017_online_CTF
- Material fingerprint: `fa06330e3a7167448ff79fc57a7b57f8f632994198d3d86d3aaa30723c4e5ec2`
- Material paths:
  - A (10):
    - `materials/attachments/IO.cpp` ← `work/materials/pwn-v11/gh-0f2902ebb6dd523a62b57f35/public/IO.cpp` (`fdd539da0806763465d9a6d30d085a0cfee19bd35f4dc7ff950bc585aa32f81e`, 1268 bytes)
    - `materials/attachments/IO.h` ← `work/materials/pwn-v11/gh-0f2902ebb6dd523a62b57f35/public/IO.h` (`9ac1c9990625f75d5bfb6b0dec6389c8d2ec2b8b951cc210b8bbba4eb04896a0`, 365 bytes)
    - `materials/attachments/VM1.cpp` ← `work/materials/pwn-v11/gh-0f2902ebb6dd523a62b57f35/public/VM1.cpp` (`42b0c5f04a791aa78c544f32e71bd1b03fb44e45cf6fbbd6036c5923970069f0`, 9488 bytes)
    - `materials/attachments/VM1.h` ← `work/materials/pwn-v11/gh-0f2902ebb6dd523a62b57f35/public/VM1.h` (`9fbef9e407c2c03f755e1f3f6417789f36d7ae9eabd760a100428480118552d4`, 108 bytes)
    - `materials/attachments/VM2.cpp` ← `work/materials/pwn-v11/gh-0f2902ebb6dd523a62b57f35/public/VM2.cpp` (`3efb7823655544e35ccafb9c27727a2417c8323651304db4cfc824ed958baf28`, 10606 bytes)
    - `materials/attachments/VM2.h` ← `work/materials/pwn-v11/gh-0f2902ebb6dd523a62b57f35/public/VM2.h` (`f6f7c4363b87bbfa176913892cf2eb2db5916bba0ea8dc7fcc0748539eb64bbc`, 108 bytes)
    - `materials/attachments/VM3.cpp` ← `work/materials/pwn-v11/gh-0f2902ebb6dd523a62b57f35/public/VM3.cpp` (`194244a0d3a457e24339965be0409c65c119117194a1713bf6d11dff97f9f6c6`, 10927 bytes)
    - `materials/attachments/VM3.h` ← `work/materials/pwn-v11/gh-0f2902ebb6dd523a62b57f35/public/VM3.h` (`15485c26051c5218e8a3b15e714412d2ea98f6ad5dbd1b4197fad36a58102eb3`, 108 bytes)
    - `materials/attachments/main.cpp` ← `work/materials/pwn-v11/gh-0f2902ebb6dd523a62b57f35/public/main.cpp` (`f885c15aa3bad454986786a5dafff73dbe00d0d3a47a5c3bdd67caa5e6b7a2bf`, 1455 bytes)
    - `materials/attachments/question.txt` ← `work/materials/pwn-v11/gh-0f2902ebb6dd523a62b57f35/public/question.txt` (`414528568e81135ed05d7881f35509759d70c8f201cb5b90d36ce1b0bad0a937`, 204 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/exploit.py` ← `work/materials/pwn-v11/gh-0f2902ebb6dd523a62b57f35/solve/exploit.py` (`37681e6e5cd03579feefdd4c302a74c829b250af8e7204924b0f5868a78a3d1a`, 8001 bytes)
  - B (1):
    - `materials/deployment/build/Makefile` ← `work/materials/pwn-v11/gh-0f2902ebb6dd523a62b57f35/build/build/Makefile` (`580de858aafc26237b14021ccb525aac0a853b2a0889528d1231a6509ed26aa9`, 475 bytes)

### 21. `gh-782a235ced7e786036e76321` — hwdbg

- Identity: cakectf / 2021 / Pwn
- Source: `kam1tsur3/2021_CTF`; `https://github.com/kam1tsur3/2021_CTF/tree/ee12843cd7901488730c41c8b313fc912cff9e46/cakectf/pwn/hwdbg`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `build_metadata`; `hybrid`; `static`; `kernel`, `shellcode_seccomp`, `vm_emulator`
- Selection reason: fills year_bucket:2020_2021; adds event cakectf; adds source kam1tsur3/2021_CTF
- Material fingerprint: `388ec82de8c862dc9415de2941013719f9864df81d98a72f17a800ddcaad1aad`
- Material paths:
  - A (26):
    - `materials/attachments/S40network` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/S40network` (`27eac7a647b151a9688d972b6668f082e1a01b699e0f6435b5fe10693135abf5`, 438 bytes)
    - `materials/attachments/S41dhcpcd` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/S41dhcpcd` (`cd5629091708cd8b1fe7908abf2c46797de313081eb8efec1365c4578e5cc68e`, 617 bytes)
    - `materials/attachments/S99ctf` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/S99ctf` (`78ee6ea7b381b49cba5d6cb5cbf666a3047c902c103b6560b9959e0528b2cbe5`, 316 bytes)
    - `materials/attachments/busybox` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/busybox` (`830578d5f4c8cd21dd3951ab32981d3e06fe09007b220e5bf53940b6dd4673bb`, 738944 bytes)
    - `materials/attachments/compress.sh` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/compress.sh` (`194aa4bdb417bd8cd99fa25d3ff2324769dcc28bd1dd9434aadb49fdbb2c7c31`, 179 bytes)
    - `materials/attachments/dhcpcd` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/dhcpcd` (`678351ca5de6f8835b20fb1b97ad636437fe375ba15be7a3a8c93113722a8b3c`, 321304 bytes)
    - `materials/attachments/dhcpcd-run-hooks` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/dhcpcd-run-hooks` (`a80479e25dac6e2e26a3804651081961b2c097fdde17e2963807cfe76603f67d`, 8136 bytes)
    - `materials/attachments/getconf` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/getconf` (`f868d86d3a4eb1f21e254991b2595f38cdb4054218ac2daee725c2ee8ae58e04`, 34496 bytes)
    - `materials/attachments/hwdbg` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/hwdbg` (`30e2089926a319fdb5ab197a166c1b167cb0bb51e4a344ce8ed240b92ba0cf89`, 26256 bytes)
    - `materials/attachments/hwdbg.__dir__.01e3f351/bzImage` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/hwdbg.__dir__.01e3f351/bzImage` (`959e45f3918157d356e71afc7c58c6ebd72c37ef1ff59149a8635d5c16150e42`, 4675056 bytes)
    - `materials/attachments/hwdbg.__dir__.01e3f351/hwdbg.c` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/hwdbg.__dir__.01e3f351/hwdbg.c` (`7f324fcbe87d7f9d5390681568462a2582ed63642a3b31749db132f1b135fd2c`, 1618 bytes)
    - `materials/attachments/hwdbg.__dir__.01e3f351/rootfs.cpio` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/hwdbg.__dir__.01e3f351/rootfs.cpio` (`f19261ff010e854cd7a7f3a7acaefdcb99b98dbb6406ec0e1af6bfd0081c161f`, 2018816 bytes)
    - `materials/attachments/hwdbg.__dir__.01e3f351/start-qemu.sh` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/hwdbg.__dir__.01e3f351/start-qemu.sh` (`6a25fd6631019ddeb00bde846b46f55514b53e46fea149edee9b848ef4a8bc98`, 302 bytes)
    - `materials/attachments/init` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/init` (`c44e502aaaf3ab77ac589729f5d6d3f08753c2c0bec990d38a35fa7b3dd082e0`, 570 bytes)
    - `materials/attachments/ld64-uClibc-1.0.38.so` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/ld64-uClibc-1.0.38.so` (`2ef08e0f9f47d127f725cc6d6694f29120d7144e172ad52722b3db0219e264ea`, 29848 bytes)
    - `materials/attachments/ldconfig` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/ldconfig` (`ccee807e2c097bc3f3c600ccd712dc1bc5a00005d785926ec932202ec3882808`, 22304 bytes)
    - `materials/attachments/ldd` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/ldd` (`0e945217be8952c9ca9903420b2a1c0b767df82f099916478e88fb2086f8261b`, 14024 bytes)
    - `materials/attachments/libatomic.so.1.2.0` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/libatomic.so.1.2.0` (`ec71103c7dbf6faa277b28d4ea534b052ffd539d617a4c26b43b9e03d0b870fa`, 26424 bytes)
    - `materials/attachments/libgcc_s.so` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/libgcc_s.so` (`69a56a9993b7729b29b274e65016031c81f2397f176ed5ad44d59bd50425e0bd`, 132 bytes)
    - `materials/attachments/libuClibc-1.0.38.so` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/libuClibc-1.0.38.so` (`aaba02f3277bfe3f8a2a2f12fafaaa7656f58b4c5fca5b4fe21e6b730a0b7e6b`, 494616 bytes)
    - `materials/attachments/nfs_check` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/nfs_check` (`c5df7c81ab887a46f60b7061f0e2374903a1aea916bdeb67d56dddc3582a704e`, 846 bytes)
    - `materials/attachments/rcK` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/rcK` (`29f26aa195e47ceaf9b505961f47227675127ce9837ff1b0139a5b49ba43e266`, 423 bytes)
    - `materials/attachments/rcS` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/rcS` (`dc1615df9f2012b20b81ffad8e07e16293039ba7fd897854ca3646d6cfea0c0f`, 408 bytes)
    - `materials/attachments/screenshot1.png` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/screenshot1.png` (`3d62c4018a7a7693c7ce38a08a8cb105e478e5af7f349416638eeceed6a8663a`, 372678 bytes)
    - `materials/attachments/start-qemu.sh` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/start-qemu.sh` (`2cb624619f6a66e8203ac430eec2fed0ead81e9083c562f91b0d968196aea27e`, 305 bytes)
    - `materials/attachments/vmlinux` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/public/vmlinux` (`776798c68c36afa3a5154547dc3465cee288dfd60125a403b2ea7511161f2b97`, 21102180 bytes)
  - W (2):
    - `materials/writeups/CakeCTF_2021.md` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/writeups/CakeCTF_2021.md` (`ce6fdc8984867ddd433f72b536aa2f8ac300a484332f5288671d2b631e1eaee7`, 16120 bytes)
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/writeups/README.md` (`3a55cd20fdf20248abb4bc2a4c0df837ec6e1067c6cb6a6efe4d6747f8778787`, 7658 bytes)
  - P (4):
    - `materials/exploit/exploit/k_exp.c` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/solve/exploit/k_exp.c` (`e13178214827af127bf36e7d6e31f8b3f13691f135f9a713df42efb7ffad0cc9`, 1652 bytes)
    - `materials/exploit/ksolve.py` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/solve/ksolve.py` (`4e417c2cd6f7b775429f8dd3de086714b238034a320e6cbb8493943214edcdaf`, 1490 bytes)
    - `materials/exploit/mnt/exploit` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/solve/mnt/exploit` (`e6ec9459e4c1fbbfbfe34e6b9004a27871670fd078021c01a508cdf409e38889`, 928504 bytes)
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/solve/solve.py` (`9403f5f0c554bae89fe37f84643db7f9ff08aef7849b099a400804c75b492b77`, 815 bytes)
  - B (2):
    - `materials/deployment/hwdbg/hwdbg.c` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/build/hwdbg/hwdbg.c` (`7f324fcbe87d7f9d5390681568462a2582ed63642a3b31749db132f1b135fd2c`, 1618 bytes)
    - `materials/deployment/hwdbg/start-qemu.sh` ← `work/materials/pwn-v11/gh-782a235ced7e786036e76321/build/hwdbg/start-qemu.sh` (`6a25fd6631019ddeb00bde846b46f55514b53e46fea149edee9b848ef4a8bc98`, 302 bytes)

### 22. `gh-5b9c34450c85a9f0fda4a921` — warmup2

- Identity: x ctf / 2016 / Pwn
- Source: `quanyang/x-ctf-2016-finals`; `https://github.com/quanyang/x-ctf-2016-finals/tree/7840c10e985b0d2ea0843105cf5291a623b03037/pwn/warmup2`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `system_libc`; `other`
- Selection reason: adds event x ctf; adds year 2016; adds source quanyang/x-ctf-2016-finals
- Material fingerprint: `c2e0863796f2bb3d313d74caefa475283bd013b3134b0859568f8b145adac744`
- Material paths:
  - A (8):
    - `materials/attachments/README.txt` ← `work/materials/pwn-v11/gh-5b9c34450c85a9f0fda4a921/public/README.txt` (`5f9e227b04a0c8d4a9b75d0fb56d7695041e4ecbfa7fbd4d186819e82e79d873`, 139 bytes)
    - `materials/attachments/dockerbuild.sh` ← `work/materials/pwn-v11/gh-5b9c34450c85a9f0fda4a921/public/dockerbuild.sh` (`29795363599bf5905fde0e20c5101dfc37ee49d7a2958c7b26bc91dcd3ef34da`, 32 bytes)
    - `materials/attachments/dockerrun.sh` ← `work/materials/pwn-v11/gh-5b9c34450c85a9f0fda4a921/public/dockerrun.sh` (`a269f58d8baeb8059fffc7d24437b3ceb8b17a45f93fe9addfe08b995c5d0805`, 44 bytes)
    - `materials/attachments/fmt` ← `work/materials/pwn-v11/gh-5b9c34450c85a9f0fda4a921/public/fmt` (`a580deccb8f65a7e741fcd25ac7c517730e3616d64020ca7c136dce0257e3a96`, 9684 bytes)
    - `materials/attachments/grader.py` ← `work/materials/pwn-v11/gh-5b9c34450c85a9f0fda4a921/public/grader.py` (`19748f04e10a351876ee1cb1ccf38a74f20b605d0242d8fada9dd165af7d739a`, 146 bytes)
    - `materials/attachments/password.txt` ← `work/materials/pwn-v11/gh-5b9c34450c85a9f0fda4a921/public/password.txt` (`67e6b6e18bbc28717cc7b5d3bf973b384200d3bc042609c89acef7821b5518b8`, 9 bytes)
    - `materials/attachments/problem.json` ← `work/materials/pwn-v11/gh-5b9c34450c85a9f0fda4a921/public/problem.json` (`b939cbc5e5b1fba4a38b280819be29934fabf17e06e8f2d23e93ce9f95002472`, 328 bytes)
    - `materials/attachments/warmup2.c` ← `work/materials/pwn-v11/gh-5b9c34450c85a9f0fda4a921/public/warmup2.c` (`0396a71c184a80962d2a254fff95e90b08cf8305dc5265bf63b57eada8482bac`, 2509 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/grader/exploit.py` ← `work/materials/pwn-v11/gh-5b9c34450c85a9f0fda4a921/solve/grader/exploit.py` (`b1b1ee01a6e4aa97668428f5d74b0e2e09765153e33d9797544ea3f83ec9a244`, 540 bytes)
  - B (5):
    - `materials/deployment/grader/deploy/Dockerfile` ← `work/materials/pwn-v11/gh-5b9c34450c85a9f0fda4a921/build/grader/deploy/Dockerfile` (`02df7981022c6e18fb89a5b5ea57eb5186be60054afa5e4df766d2f967677ab5`, 586 bytes)
    - `materials/deployment/grader/deploy/dockerbuild.sh` ← `work/materials/pwn-v11/gh-5b9c34450c85a9f0fda4a921/build/grader/deploy/dockerbuild.sh` (`29795363599bf5905fde0e20c5101dfc37ee49d7a2958c7b26bc91dcd3ef34da`, 32 bytes)
    - `materials/deployment/grader/deploy/dockerrun.sh` ← `work/materials/pwn-v11/gh-5b9c34450c85a9f0fda4a921/build/grader/deploy/dockerrun.sh` (`a269f58d8baeb8059fffc7d24437b3ceb8b17a45f93fe9addfe08b995c5d0805`, 44 bytes)
    - `materials/deployment/grader/grader.py` ← `work/materials/pwn-v11/gh-5b9c34450c85a9f0fda4a921/build/grader/grader.py` (`19748f04e10a351876ee1cb1ccf38a74f20b605d0242d8fada9dd165af7d739a`, 146 bytes)
    - `materials/deployment/grader/warmup2.c` ← `work/materials/pwn-v11/gh-5b9c34450c85a9f0fda4a921/build/grader/warmup2.c` (`0396a71c184a80962d2a254fff95e90b08cf8305dc5265bf63b57eada8482bac`, 2509 bytes)

### 23. `saj-2023-pwn-full-chain-wall-sina` — Full_Chain_Wall_Sina

- Identity: HITCON / 2023 / Pwn
- Source: `hitconctf/ctf2023.hitcon.org`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/HITCON/2023/Quals/pwn/Full_Chain_Wall_Sina`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `bundled_libc_loader`; `format_string`, `shellcode_seccomp`, `stack_rop`, `vm_emulator`
- Selection reason: fills year_bucket:2023; adds event HITCON; adds source hitconctf/ctf2023.hitcon.org
- Material fingerprint: `c337280f2df18fe1c7eb84cfbddb41d34e4a50d008f8556e6b7770ef0929fea4`
- Material paths:
  - A (13):
    - `materials/attachments/README.md` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/public/README.md` (`cdf72c52704b6ab2ab127ba96d32c18647c6266db50ba70f6c65d5e7d9192146`, 2297 bytes)
    - `materials/attachments/bios-256k.bin` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/public/bios-256k.bin` (`2b864f5b202625b03bdf152322c7ecabcde1413e62bd0987970bded9cc915184`, 262144 bytes)
    - `materials/attachments/bzImage` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/public/bzImage` (`06b10f33b633da5bf6f6dabec9fa308892fabf26ddc56a1c5aa1f5120ea3352f`, 15748352 bytes)
    - `materials/attachments/efi-e1000.rom` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/public/efi-e1000.rom` (`f37222fcdf0481bfbaf7a16d9aaf740aeb41d3d24c187801eb6e9a628cec0fc8`, 159232 bytes)
    - `materials/attachments/initramfs.cpio` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/public/initramfs.cpio` (`e54d9f6359717cecb857ce4f12974c81b07ccf848a0a6e3afc9dd564dbbb9370`, 21561856 bytes)
    - `materials/attachments/kvmvapic.bin` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/public/kvmvapic.bin` (`cdf057a71b07e3b52b19cbe210bdefa59250d01a9810b960f7fe1f98eed95a27`, 9216 bytes)
    - `materials/attachments/ld-linux-x86-64.so.2` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/public/ld-linux-x86-64.so.2` (`2300cd4d6401355eb167d80b4b260f3262a4d981af9620d89b0f2b05d9421800`, 1367936 bytes)
    - `materials/attachments/libc.so.6` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/public/libc.so.6` (`ea4b2b5e79d556edb366185d0a1c6b248ed6d17cbe8c2e63b63fa47e5e0ffafc`, 12657912 bytes)
    - `materials/attachments/linuxboot_dma.bin` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/public/linuxboot_dma.bin` (`9c49e255340c78fc12e54ed043462bca02fb7fca29b7cfab62ff88a5344b6950`, 1536 bytes)
    - `materials/attachments/sina` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/public/sina` (`37264531b6f99c481badaadd8874b9ba6a6d6d87927a275fc8762b9b5bdfe126`, 14392 bytes)
    - `materials/attachments/sina.c` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/public/sina.c` (`fbde255c72048beaac2b90b2e9c446c4a974a6ae93862db67d322d7a5a7e8011`, 165 bytes)
    - `materials/attachments/sina_patched` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/public/sina_patched` (`f1acfe977183798b249aadbc2258efa25b7dfce0f97aae6b14b7e8624d1cfa59`, 21177 bytes)
    - `materials/attachments/vgabios-stdvga.bin` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/public/vgabios-stdvga.bin` (`e13dafa0bd55d3d8632f278d87272122db18cbd5675307002c28636d597e2d1e`, 39936 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/writeups/README.md` (`47998d501ba9ee28cee23e52b0944d730c56044b78f7fb512564bb9f963bbedb`, 3675 bytes)
  - P (2):
    - `materials/exploit/exploit.c` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/solve/exploit.c` (`b53ce74be25bf6633508e1feaf2929e9057de21a21c4518c3428b7bf595c0891`, 12565 bytes)
    - `materials/exploit/working.exploit.py` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/solve/working.exploit.py` (`552c29eddceb2d157ebec78dfc33e1462dec30a6dcf96311afc6f07d59896088`, 3671 bytes)
  - B (5):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/build/Dockerfile` (`2ca767f66e2f530dfd03b758744ed98ffb49dd8f9c4f7e75d2749ecc6a56a6ad`, 419 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/build/docker-compose.yml` (`b5fc0e97c12911b9943c2e04a5e9268183edd97ce7d4b08cb9efd2ee15dc6a11`, 105 bytes)
    - `materials/deployment/share/run.sh` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/build/share/run.sh` (`fe7797a00d3f96cb06d20cb2d6089b95985ecbaa3b0084346bd04c6ad992193e`, 350 bytes)
    - `materials/deployment/src/sina.c` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/build/src/sina.c` (`fbde255c72048beaac2b90b2e9c446c4a974a6ae93862db67d322d7a5a7e8011`, 165 bytes)
    - `materials/deployment/xinetd` ← `work/materials/pwn-v11/saj-2023-pwn-full-chain-wall-sina/build/xinetd` (`85bd67f8ae14d974fe2702a4c77779b0e4d7d716ff9020b8543bd43da02f6ffe`, 176 bytes)

### 24. `saj-2022-pwn-pointytail` — pointytail

- Identity: SEETF / 2022 / Pwn
- Source: `Social-Engineering-Experts/SEETF-2022-Public`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/SEETF/2022/pwn/pointytail`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile_compose`; `nonstandard`; `unknown_or_non_elf`; `other`
- Selection reason: fills year_bucket:2022; adds event SEETF; adds source Social-Engineering-Experts/SEETF-2022-Public
- Material fingerprint: `f9649155cdbfc36d6b75475d84d72c53f1e2d45d983ff8607f02e9ff19e48525`
- Material paths:
  - A (2):
    - `materials/attachments/pointytail.dll` ← `work/materials/pwn-v11/saj-2022-pwn-pointytail/public/pointytail.dll` (`0228032dc41ee5fde2ddf2fe70c73e4166525e4206b40d46235d4588a8f3f4da`, 3072 bytes)
    - `materials/attachments/pointytail.runtimeconfig.json` ← `work/materials/pwn-v11/saj-2022-pwn-pointytail/public/pointytail.runtimeconfig.json` (`0d8ca052170b1eefdf8978d22a115ed9620ac5ebdfb5a8b7b2207e2b8fb0e2cb`, 118 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solve.ipynb` ← `work/materials/pwn-v11/saj-2022-pwn-pointytail/solve/solve.ipynb` (`bc355a705fd63fa5a6fc3552a407391ec8856b3cd7cb2683f9fa4b29302a677f`, 7746 bytes)
  - B (2):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2022-pwn-pointytail/build/Dockerfile` (`b74c3638bd2d69966c1851cd47b564054c6ddbdbd49fad02e5a53eee28d59837`, 383 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/saj-2022-pwn-pointytail/build/docker-compose.yml` (`8aee77c56c205b02a32bdd0363f4e9c0b1ca7bb6f7d292a467d46915a4a5c599`, 71 bytes)

### 25. `saj-2024-pwn-backup-power` — Backup_Power

- Identity: UIUCTF / 2024 / Pwn
- Source: `sigpwny/2024-ectf-uiuc`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/UIUCTF/2024/pwn/Backup_Power`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `static`; `format_string`, `stack_rop`, `vm_emulator`
- Selection reason: fills year_bucket:2024; adds event UIUCTF; adds source sigpwny/2024-ectf-uiuc
- Material fingerprint: `fa7df8888070d045a3241e16156f23e6ddf04ce287ce3e29c77eba789895cace`
- Material paths:
  - A (5):
    - `materials/attachments/README.md` ← `work/materials/pwn-v11/saj-2024-pwn-backup-power/public/README.md` (`9dff503056a00cf02afaaedd7c05cac1bdbee126fcbe0b737b3440c2d2580964`, 105 bytes)
    - `materials/attachments/backup-power` ← `work/materials/pwn-v11/saj-2024-pwn-backup-power/public/backup-power` (`e3e73ab1b83190709302b613725881ed8937b73331b91afb0c9745bf20fba43b`, 692584 bytes)
    - `materials/attachments/backup-power.c` ← `work/materials/pwn-v11/saj-2024-pwn-backup-power/public/backup-power.c` (`fd9e64d5a662ac3191fc990c6e5ad56ffa1dc46e2d871e233a190aa477936625`, 4565 bytes)
    - `materials/attachments/do.py` ← `work/materials/pwn-v11/saj-2024-pwn-backup-power/public/do.py` (`d77c43bb0b1c061a803147e1f5ff2d6a5a9559710ba751fc26421811ca82f672`, 1256 bytes)
    - `materials/attachments/gadgets.txt` ← `work/materials/pwn-v11/saj-2024-pwn-backup-power/public/gadgets.txt` (`e895f962047037427db411c151a6b64189cc046ade664159dfbca8e6b3ce678a`, 28141 bytes)
  - W (2):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2024-pwn-backup-power/writeups/README.md` (`fcf628753a11287f752be0b295ce1845f4d1defaca9f4e166ce454bf7df2c716`, 13453 bytes)
    - `materials/writeups/SOLVE.md` ← `work/materials/pwn-v11/saj-2024-pwn-backup-power/writeups/SOLVE.md` (`e4c190b90474840c433b118460e88bd32cc118cea3e1d9c968a5fc29a149e000`, 2023 bytes)
  - P (5):
    - `materials/exploit/SOLVE.md` ← `work/materials/pwn-v11/saj-2024-pwn-backup-power/solve/SOLVE.md` (`e4c190b90474840c433b118460e88bd32cc118cea3e1d9c968a5fc29a149e000`, 2023 bytes)
    - `materials/exploit/solve.0ea36057.py` ← `work/materials/pwn-v11/saj-2024-pwn-backup-power/solve/solve.0ea36057.py` (`1ad76725df7c08d86b1a5ee221eb876d475f2a1eb2eee663026bb3218218ea89`, 1316 bytes)
    - `materials/exploit/solve.9e9918ce.py` ← `work/materials/pwn-v11/saj-2024-pwn-backup-power/solve/solve.9e9918ce.py` (`e6380037c5f306e0fecb6946943e1fbfeae9027b6b30b8fd5a94ae2a255b79cd`, 958 bytes)
    - `materials/exploit/solve.f9ae65c7.py` ← `work/materials/pwn-v11/saj-2024-pwn-backup-power/solve/solve.f9ae65c7.py` (`3690ddde9ccede2679ebcec5fab7f953bd8ee4628e04d309e47794d2ab51ceac`, 2200 bytes)
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2024-pwn-backup-power/solve/solve.py` (`5c9e1c8370d60b5b350be3d6eee3fd56b5f8814a9c155bee4b2a01e4ee40d0be`, 1022 bytes)
  - B (7):
    - `materials/deployment/challenge/Dockerfile` ← `work/materials/pwn-v11/saj-2024-pwn-backup-power/build/challenge/Dockerfile` (`20ac1f04f8dc3af5bfa45b8b323130ef69885662f1839ab6d9e068d2107127d4`, 586 bytes)
    - `materials/deployment/challenge/Makefile` ← `work/materials/pwn-v11/saj-2024-pwn-backup-power/build/challenge/Makefile` (`cefa252477fc07813b530b8cdffd851482c13dd98385564b38fac85075117e71`, 187 bytes)
    - `materials/deployment/challenge/backup-power.c` ← `work/materials/pwn-v11/saj-2024-pwn-backup-power/build/challenge/backup-power.c` (`fd9e64d5a662ac3191fc990c6e5ad56ffa1dc46e2d871e233a190aa477936625`, 4565 bytes)
    - `materials/deployment/healthcheck/Dockerfile` ← `work/materials/pwn-v11/saj-2024-pwn-backup-power/build/healthcheck/Dockerfile` (`97d3b6793503fa5f24a92732aa148013001045a754aab19421e0b7c06c99c3e5`, 843 bytes)
    - `materials/deployment/healthcheck/healthcheck.py` ← `work/materials/pwn-v11/saj-2024-pwn-backup-power/build/healthcheck/healthcheck.py` (`751eec5c4d5e50b149907dc6796715465e19c5a0c2202b852505d27649b9f9fc`, 1673 bytes)
    - `materials/deployment/healthcheck/healthcheck_loop.sh` ← `work/materials/pwn-v11/saj-2024-pwn-backup-power/build/healthcheck/healthcheck_loop.sh` (`f26fd678c224089b30c7a8049d96d42883344be9e998f80bc02e8676d63e1ce5`, 896 bytes)
    - `materials/deployment/healthcheck/healthz_webserver.py` ← `work/materials/pwn-v11/saj-2024-pwn-backup-power/build/healthcheck/healthz_webserver.py` (`50810e810d849d2a451a223402297d8b777794ef028b601e22447e23604ea56a`, 1388 bytes)

### 26. `saj-2022-pwn-babyheapng` — babyheapng

- Identity: TJCTF / 2022 / Pwn
- Source: `TJCSec/tjctf-2022-challenges`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/TJCTF/2022/pwn/babyheapng`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `prebuilt_rehost`; `musl`; `other`
- Selection reason: adds event TJCTF; adds source TJCSec/tjctf-2022-challenges
- Material fingerprint: `4a574bfba9d6806eaaf0d0271e6fecfc056e5de213b7a1136cb2a6fe383d023a`
- Material paths:
  - A (3):
    - `materials/attachments/.dockerignore` ← `work/materials/pwn-v11/saj-2022-pwn-babyheapng/public/.dockerignore` (`4eb3d23f87d80725d28c9bfcb73139f2b9ee0e95dd1ccb5b17d478c1f9cafa7b`, 42 bytes)
    - `materials/attachments/chall` ← `work/materials/pwn-v11/saj-2022-pwn-babyheapng/public/chall` (`fb87be42607a88dfef272bf5ca304a6ac2121b9652b16b8a757158abb4ccd372`, 18984 bytes)
    - `materials/attachments/challenge.yaml` ← `work/materials/pwn-v11/saj-2022-pwn-babyheapng/public/challenge.yaml` (`9c1958b2fd22abe142fc00e6b72614256c5c3365e85967312cf27e81cd9827f9`, 733 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solve/solve.py` ← `work/materials/pwn-v11/saj-2022-pwn-babyheapng/solve/solve/solve.py` (`c36f25be75f4093917a525d36468e6cd102dc93c80dc98f0f42c64bf6299956b`, 2992 bytes)
  - B (1):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2022-pwn-babyheapng/build/Dockerfile` (`8feb7c6ace121c9349954f3d97b60bf3bb20739ae3828be73eb48a14c64a6bbe`, 294 bytes)

### 27. `gh-7a7e006afd0b331da2a4be1f` — blazeme

- Identity: Blaze CTF / 2018 / Pwn
- Source: `0xbada/ctfrepo`; `https://github.com/0xbada/ctfrepo/tree/f1db7c952e0a03beab0269d47047e692ff6eb464/2018/Blaze CTF 2018/pwn/blazeme`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `build_metadata`; `source_build`; `unknown_or_non_elf`; `kernel`, `shellcode_seccomp`, `stack_rop`
- Selection reason: adds event Blaze CTF; adds source 0xbada/ctfrepo
- Material fingerprint: `b7f7bd27b893b31a305c04ae180023cc64af1c7a7d8edb4aabacf553e5a0302b`
- Material paths:
  - A (4):
    - `materials/attachments/images/blazeme.c` ← `work/materials/pwn-v11/gh-7a7e006afd0b331da2a4be1f/public/images/blazeme.c` (`e17bce6ca8ac9e0592112ac5423574cad5f1a014c81b6e64ff074dc72197f791`, 3481 bytes)
    - `materials/attachments/images/bzImage` ← `work/materials/pwn-v11/gh-7a7e006afd0b331da2a4be1f/public/images/bzImage` (`15703b6937d2dbe6355bbfdbb9f0ba6f13a5474cdd4a974fb96a97e663aef874`, 4227024 bytes)
    - `materials/attachments/images/rootfs.ext2` ← `work/materials/pwn-v11/gh-7a7e006afd0b331da2a4be1f/public/images/rootfs.ext2` (`b28ba2ccc58b7ef056358f891d8577e05b73943b78e3358c6bed87fd7586fd35`, 62914560 bytes)
    - `materials/attachments/solv.c` ← `work/materials/pwn-v11/gh-7a7e006afd0b331da2a4be1f/public/solv.c` (`051279876680ebf55b49dcd8a1fafd510360592e3a06fa22da6ed8b0f49be713`, 1879 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/gh-7a7e006afd0b331da2a4be1f/writeups/README.md` (`55582f925b8e036a358ca41eb040c26111e77775a2d48ff1804ad6dca34086ec`, 5321 bytes)
  - P (1):
    - `materials/exploit/exploit.c` ← `work/materials/pwn-v11/gh-7a7e006afd0b331da2a4be1f/solve/exploit.c` (`48b9768c9f407a5544892c4409279603f3c67952e5260ba0d1a457aa28297f25`, 3510 bytes)
  - B (2):
    - `materials/deployment/images/blazeme.c` ← `work/materials/pwn-v11/gh-7a7e006afd0b331da2a4be1f/build/images/blazeme.c` (`e17bce6ca8ac9e0592112ac5423574cad5f1a014c81b6e64ff074dc72197f791`, 3481 bytes)
    - `materials/deployment/images/run.sh` ← `work/materials/pwn-v11/gh-7a7e006afd0b331da2a4be1f/build/images/run.sh` (`99aacda5db32cbc889561a9023f79a8b4afb130b26baec6504213c1c7b6ded7d`, 233 bytes)

### 28. `gh-4b21898e8a2d18878d06a239` — kpwn-1

- Identity: Fennec CTF / 2026 / Pwn
- Source: `Underr00ted/Fennec-CTF-2026-challenges`; `https://github.com/Underr00ted/Fennec-CTF-2026-challenges/tree/3f48a886c0b66147008f601ecb1dc44646636cbf/pwn/kpwn-1`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `static`; `kernel`, `stack_rop`, `vm_emulator`
- Selection reason: adds event Fennec CTF; adds source Underr00ted/Fennec-CTF-2026-challenges
- Material fingerprint: `8a52e0f2f2c248859611ab812c636606825d29c1e189087f2cd2c5100a859665`
- Material paths:
  - A (9):
    - `materials/attachments/build-artifacts.sh` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/public/build-artifacts.sh` (`8b9630aecdc06f2770e19bdddcb305f0ba7cd5c6f4b06b62038964ec0432a76a`, 471 bytes)
    - `materials/attachments/build-fs.sh` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/public/build-fs.sh` (`56083216972d65508735bb8625f6452e2a3be68d458ba30d31d4bba8c7682d4e`, 8712 bytes)
    - `materials/attachments/build-kernel.sh` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/public/build-kernel.sh` (`d1ba2130e3b8a6bddcbeedbe8e517032e5d146692d811d9dc04edebe2ac78a7d`, 2871 bytes)
    - `materials/attachments/bzImage` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/public/bzImage` (`f55d29c516fddb1d4e08987b48faabfe8c0a1f2b69a9c2d1dd482104022f6f4e`, 14246912 bytes)
    - `materials/attachments/chall.c` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/public/chall.c` (`38bcaee9e4409c53f7b28c019df1b0f16bd33ae70c35488df46bf76c35f96dd4`, 2641 bytes)
    - `materials/attachments/chall.ko` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/public/chall.ko` (`269443d702ccd55cbbe28a95128ee4507be3220cb8164736d8b4279d133d9741`, 10296 bytes)
    - `materials/attachments/rootfs.cpio` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/public/rootfs.cpio` (`47294ed06df3e7719c7567051834bba12e31e561265366073ab84fafe15d80e0`, 2542080 bytes)
    - `materials/attachments/run-qemu.sh` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/public/run-qemu.sh` (`e298b50165f0d9bbea2b81498b50e220e486fdef83188b03808baa8a2d0e47d5`, 300 bytes)
    - `materials/attachments/vmlinux` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/public/vmlinux` (`7ea4e69bf7cf9ad2542423c161ded2e0498918beb90a0a2d2e643a7d24147f03`, 52129384 bytes)
  - W: absent
  - P (3):
    - `materials/exploit/solve/exploit` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/solve/solve/exploit` (`7b6b7affdfba5c5b51276d18c2c899055eadcf3d4d3a3a1f2e338a842aceb68a`, 864592 bytes)
    - `materials/exploit/solve/exploit.c` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/solve/solve/exploit.c` (`7ae793937ff64700463ce11bfe03d44059ad9d7e46c5057e13dfdecdad6b8d1e`, 3274 bytes)
    - `materials/exploit/solve/exploit.py` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/solve/solve/exploit.py` (`09ee41b021633c1540cca396761a15849cda73347f1e279554fdacc6c70faa84`, 1151 bytes)
  - B (8):
    - `materials/deployment/challenge/Dockerfile` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/build/challenge/Dockerfile` (`7507046a3d9b049fdbd6c57373fbd4d2970ceafa77e528e79858518116b1edb1`, 818 bytes)
    - `materials/deployment/challenge/build/build-artifacts.sh` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/build/challenge/build/build-artifacts.sh` (`8b9630aecdc06f2770e19bdddcb305f0ba7cd5c6f4b06b62038964ec0432a76a`, 471 bytes)
    - `materials/deployment/challenge/build/build-fs.sh` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/build/challenge/build/build-fs.sh` (`56083216972d65508735bb8625f6452e2a3be68d458ba30d31d4bba8c7682d4e`, 8712 bytes)
    - `materials/deployment/challenge/build/build-kernel.sh` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/build/challenge/build/build-kernel.sh` (`d1ba2130e3b8a6bddcbeedbe8e517032e5d146692d811d9dc04edebe2ac78a7d`, 2871 bytes)
    - `materials/deployment/challenge/build/build.sh` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/build/challenge/build/build.sh` (`5e5f0c04e55af69586affca991ebcc987b993729396f2d8331b22303e753dbab`, 608 bytes)
    - `materials/deployment/challenge/chall.c` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/build/challenge/chall.c` (`38bcaee9e4409c53f7b28c019df1b0f16bd33ae70c35488df46bf76c35f96dd4`, 2641 bytes)
    - `materials/deployment/challenge/docker-compose.yml` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/build/challenge/docker-compose.yml` (`bc9a55480f239013fa83a1d421ecd4c8f808f2cf12c36352b536cf0617323ba3`, 179 bytes)
    - `materials/deployment/challenge/run-qemu.sh` ← `work/materials/pwn-v11/gh-4b21898e8a2d18878d06a239/build/challenge/run-qemu.sh` (`e298b50165f0d9bbea2b81498b50e220e486fdef83188b03808baa8a2d0e47d5`, 300 bytes)

### 29. `gh-8c1099152bc23db3ebb9f4a6` — Dragon Quest

- Identity: m0lecon beginners / 2025 / Pwn
- Source: `TheDeppSide/my-challs`; `https://github.com/TheDeppSide/my-challs/tree/953ce154a124031e87510224ba42972b919c8d16/m0lecon_beginners_2025/pwn/Dragon_Quest`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `compose`; `hybrid`; `bundled_libc_loader`; `other`
- Selection reason: adds event m0lecon beginners; adds source TheDeppSide/my-challs
- Material fingerprint: `79e6f2569879f5797ee51ffd69cd48bf176481006faeb79adde6ffb42a5a93c2`
- Material paths:
  - A (4):
    - `materials/attachments/chall` ← `work/materials/pwn-v11/gh-8c1099152bc23db3ebb9f4a6/public/chall` (`dce4862e174aac55cf8038877f8a5ac3cc9295bb7228a4eaeb90e56c85a08950`, 16800 bytes)
    - `materials/attachments/chall.c` ← `work/materials/pwn-v11/gh-8c1099152bc23db3ebb9f4a6/public/chall.c` (`ca3769ccb4b6a5354c06c3ed5b390d8d6d51aeb0ac71382ff87c72049345648f`, 7690 bytes)
    - `materials/attachments/ld-linux-x86-64.so.2` ← `work/materials/pwn-v11/gh-8c1099152bc23db3ebb9f4a6/public/ld-linux-x86-64.so.2` (`6222a16be7f2d458d6870efe6e715fc0c8d45766fb79cf7dcc3125538d703e28`, 236616 bytes)
    - `materials/attachments/libc.so.6` ← `work/materials/pwn-v11/gh-8c1099152bc23db3ebb9f4a6/public/libc.so.6` (`511f825ee075610ac9c0f7f91e2c13de2000d0f7b859f6461137e809a0a009d0`, 2125328 bytes)
  - W (1):
    - `materials/writeups/writeup.md` ← `work/materials/pwn-v11/gh-8c1099152bc23db3ebb9f4a6/writeups/writeup.md` (`fe85e78957b01ec4513b235c78d7ade21494598563f32f31b7e804413d3d84ba`, 5082 bytes)
  - P (1):
    - `materials/exploit/exploit/solve.py` ← `work/materials/pwn-v11/gh-8c1099152bc23db3ebb9f4a6/solve/exploit/solve.py` (`2dd5f160cc7e3d78a1927a78f442a8914655518c23a0c089923ebafab56d87c6`, 1068 bytes)
  - B (2):
    - `materials/deployment/src/chall.c` ← `work/materials/pwn-v11/gh-8c1099152bc23db3ebb9f4a6/build/src/chall.c` (`ca3769ccb4b6a5354c06c3ed5b390d8d6d51aeb0ac71382ff87c72049345648f`, 7690 bytes)
    - `materials/deployment/src/docker-compose.yml` ← `work/materials/pwn-v11/gh-8c1099152bc23db3ebb9f4a6/build/src/docker-compose.yml` (`e1000c4cadec485eaedef908f302a531d46827d7c95fee4fd56b58b183ebf0da`, 768 bytes)

### 30. `gh-46626c6f2dcb825e16557526` — Return Of The ROPs

- Identity: 0x41414141 / 2021 / Pwn
- Source: `acdwas/ctf`; `https://github.com/acdwas/ctf/tree/da99769500d589ac6c6909c37a3b4f731cf51bbd/2021/0x41414141/pwn/Return Of The ROPs`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `build_metadata`; `hybrid`; `bundled_loader_only`; `stack_rop`
- Selection reason: adds event 0x41414141; adds source acdwas/ctf
- Material fingerprint: `e13d158444643d669aa1e2faa671376cea90487e8524a2119a476731b744eb31`
- Material paths:
  - A (7):
    - `materials/attachments/PoW` ← `work/materials/pwn-v11/gh-46626c6f2dcb825e16557526/public/PoW` (`387c95f8b411acab47d20e4ae29c2380955c00cecd4041a91fb6b3dadb83d444`, 17864 bytes)
    - `materials/attachments/PoW.428ebd74` ← `work/materials/pwn-v11/gh-46626c6f2dcb825e16557526/public/PoW.428ebd74` (`8bf80337d2fbc82e2993a074c15be5ee4ca868e4215771815a3b32a1a1ec92ec`, 17392 bytes)
    - `materials/attachments/ld-2.31.so` ← `work/materials/pwn-v11/gh-46626c6f2dcb825e16557526/public/ld-2.31.so` (`0570796b6aaef493b906dc2150e496480d24fbb979596e88c48af537451b0c2a`, 191472 bytes)
    - `materials/attachments/libc6_2.31-0ubuntu7_amd64.so` ← `work/materials/pwn-v11/gh-46626c6f2dcb825e16557526/public/libc6_2.31-0ubuntu7_amd64.so` (`7327f637f3ccbd9ea275cccd9f444d69876facb87f41efbddebe197ded7e4602`, 19383256 bytes)
    - `materials/attachments/main.sh` ← `work/materials/pwn-v11/gh-46626c6f2dcb825e16557526/public/main.sh` (`e2d8a2a16b76fefe509ad6ec12637c05eef3b34ce996c7da2a42db3390f88e36`, 81 bytes)
    - `materials/attachments/ret-of-the-rops` ← `work/materials/pwn-v11/gh-46626c6f2dcb825e16557526/public/ret-of-the-rops` (`fb5621a95f6ae9906fbb5edbdb7943ef5c15ae6ba3b95669d5a92377b19c390b`, 16984 bytes)
    - `materials/attachments/ret-of-the-rops.py` ← `work/materials/pwn-v11/gh-46626c6f2dcb825e16557526/public/ret-of-the-rops.py` (`02e323a5cfe215189021cb80c87f4ee2c51db6944922782132d48cc5e99c533a`, 1149 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/exploit.py` ← `work/materials/pwn-v11/gh-46626c6f2dcb825e16557526/solve/exploit.py` (`9bb4db86b6d2d754e32c557bbd992ba1b01a5825c8661e048c1e7a31b0a977ca`, 1299 bytes)
  - B (1):
    - `materials/deployment/main.sh` ← `work/materials/pwn-v11/gh-46626c6f2dcb825e16557526/build/main.sh` (`e2d8a2a16b76fefe509ad6ec12637c05eef3b34ce996c7da2a42db3390f88e36`, 81 bytes)

## Automated verification

The verifier recomputes the deterministic selection from the formal database, checks 15/15 quotas, canonical identities, route mappings, role states, unique IDs/material fingerprints, every source and dataset path, byte size, SHA-256, archive integrity, task contracts, and report coverage.

```bash
python examples/build_target/scripts/materialize_p1_control_subset.py verify
```

Static A/W/P/B evidence is inventory only; none of these tasks is reported as R3, R4, R5, or any X tier.
