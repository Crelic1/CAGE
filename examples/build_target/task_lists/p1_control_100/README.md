# P1 AWPB/APB 100-task control subset

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
- Selection SHA-256: `3326c822d8a60925ef07ff76fa8f28cc2a8b4f8313b86e83ee33b07a0d9cdc97`

Generation command:

```bash
python examples/build_target/scripts/materialize_p1_control_subset.py generate --source-root /mnt/olddata/home/yihe/workspace/ctf-env-collection --dataset .cage/build-target/p1-awpb-apb-100 --manifest examples/build_target/task_lists/p1_control_100/manifest.json --report examples/build_target/task_lists/p1_control_100/README.md --count 100 --seed cage-build-target-p1-awpb-apb-30-v1
```

## Distribution

- Profiles: `APB` 50, `AWPB` 50
- Unique events: 100
- Unique source repositories: 100
- Years: `2015` 1, `2016` 1, `2017` 1, `2018` 2, `2019` 4, `2020` 6, `2021` 12, `2022` 13, `2023` 17, `2024` 18, `2025` 16, `2026` 9
- Build forms: `build_metadata` 16, `compose` 2, `dockerfile` 40, `dockerfile_compose` 42
- Build modes: `hybrid` 65, `nonstandard` 4, `prebuilt_rehost` 11, `source_build` 20
- Runtime forms: `bundled_libc_loader` 16, `bundled_libc_only` 14, `bundled_loader_only` 8, `musl` 7, `static` 14, `system_libc` 25, `unknown_or_non_elf` 16
- Exploit classes: `format_string` 12, `heap` 24, `kernel` 10, `other` 29, `shellcode_seccomp` 25, `stack_rop` 42, `vm_emulator` 12
- Topology: `multi_service` 10, `single_service` 90
- Complexity: `large` 15, `medium` 38, `small` 47

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
| 31 | `gh-a413f013eb02fb618a538106` | `AWPB` / `fast_track_full` | `tsg-ut/tsgctf2020` / tsgctf / 2020 | `dockerfile_compose`, `hybrid` | `bundled_libc_only` | heap | `multi_service` | 24 / 6.7 MiB |
| 32 | `gh-c4c32267c212dedfa844cff2` | `APB` / `fast_track_no_writeup` | `0xStraw-Hat/pwn-challenges` / 0xfun26 / 2026 | `dockerfile`, `nonstandard` | `bundled_libc_loader` | other | `single_service` | 4 / 2.3 MiB |
| 33 | `saj-2025-pwn-nitebus` | `AWPB` / `fast_track_full` | `Cryptonite-MIT/niteCTF-2025` / niteCTF / 2025 | `dockerfile`, `prebuilt_rehost` | `static` | format_string, shellcode_seccomp, vm_emulator | `single_service` | 6 / 803.7 KiB |
| 34 | `saj-2025-pwn-canon-event` | `APB` / `fast_track_no_writeup` | `TheRomanXpl0it/TRX-CTF-2025` / TRX / 2025 | `compose`, `hybrid` | `bundled_libc_loader` | shellcode_seccomp | `single_service` | 10 / 3.2 MiB |
| 35 | `saj-2020-pwn-guessinggame2` | `AWPB` / `fast_track_full` | `picoCTF/picoCTF` / picoCTF / 2020 | `build_metadata`, `hybrid` | `bundled_loader_only` | format_string, stack_rop | `single_service` | 9 / 6.2 MiB |
| 36 | `saj-2024-pwn-faulty-kernel` | `APB` / `fast_track_no_writeup` | `DownUnderCTF/Challenges_2024_Public` / DownUnderCTF / 2024 | `dockerfile_compose`, `source_build` | `musl` | kernel | `single_service` | 12 / 18.4 MiB |
| 37 | `gh-1b722a3400c6597cac56e5c9` | `AWPB` / `fast_track_full` | `tj-oconnor/cyber-open-2022` / cyber open / 2022 | `dockerfile_compose`, `hybrid` | `bundled_libc_only` | stack_rop | `multi_service` | 19 / 1.9 MiB |
| 38 | `gh-270f15f0791a91b244cdffc1` | `APB` / `fast_track_no_writeup` | `koromaki88/ctf-archive` / b / 2025 | `dockerfile`, `nonstandard` | `unknown_or_non_elf` | other | `single_service` | 3 / 2.5 KiB |
| 39 | `saj-2024-pwn-drone-adventure` | `AWPB` / `fast_track_full` | `SunshineCTF/SunshineCTF-2022-Public` / SunshineCTF / 2024 | `build_metadata`, `hybrid` | `bundled_loader_only` | stack_rop | `single_service` | 10 / 6.2 MiB |
| 40 | `saj-2021-pwn-house-of-tataru` | `APB` / `fast_track_no_writeup` | `Nu1LCTF/n1ctf-2021` / N1CTF / 2021 | `dockerfile_compose`, `prebuilt_rehost` | `musl` | heap, stack_rop | `single_service` | 5 / 738.0 KiB |
| 41 | `gh-bcbf8e4258381230e5ce1de7` | `AWPB` / `fast_track_full` | `NUSGreyhats/greyctf26-challs-public` / greyctf26 / 2026 | `dockerfile_compose`, `hybrid` | `system_libc` | heap | `multi_service` | 13 / 134.7 KiB |
| 42 | `saj-2021-pwn-middleagedheap` | `APB` / `fast_track_no_writeup` | `b01lers/b01lers-ctf-2021` / b01lers / 2021 | `dockerfile_compose`, `hybrid` | `bundled_libc_only` | stack_rop | `multi_service` | 12 / 1.9 MiB |
| 43 | `saj-2025-pwn-outdated` | `AWPB` / `fast_track_full` | `project-sekai-ctf/sekaictf-2025` / SekaiCTF / 2025 | `dockerfile_compose`, `hybrid` | `musl` | vm_emulator | `single_service` | 10 / 982.2 KiB |
| 44 | `gh-0e6a64119220530e1d497576` | `APB` / `fast_track_no_writeup` | `maulvialf/CTF-Challs-Archive` / CJ CTF / 2020 | `dockerfile_compose`, `nonstandard` | `unknown_or_non_elf` | other | `single_service` | 6 / 11.0 KiB |
| 45 | `saj-2021-pwn-university-pwn` | `AWPB` / `fast_track_full` | `jopraveen/TamilCTF2021` / Tamil / 2021 | `dockerfile`, `hybrid` | `bundled_loader_only` | heap | `single_service` | 20 / 2.3 MiB |
| 46 | `gh-46a73bbde9c0c5b1eaf50a85` | `APB` / `fast_track_no_writeup` | `hax1ng/hxpctf2025` / hxpctf / 2025 | `dockerfile_compose`, `prebuilt_rehost` | `musl` | shellcode_seccomp, stack_rop | `single_service` | 6 / 44.8 KiB |
| 47 | `saj-2024-pwn-fl-support-center` | `AWPB` / `fast_track_full` | `tsg-ut/tsgctf` / TSG / 2024 | `dockerfile_compose`, `hybrid` | `system_libc` | heap | `multi_service` | 10 / 89.8 KiB |
| 48 | `saj-2026-pwn-goodbye-libc` | `APB` / `fast_track_no_writeup` | `tamuctf/tamuctf-2024` / TAMUctf / 2026 | `build_metadata`, `hybrid` | `bundled_loader_only` | other | `single_service` | 10 / 249.9 KiB |
| 49 | `saj-2023-pwn-n0tes-revenge` | `AWPB` / `fast_track_full` | `bsidestlv/ctf20-public` / BSidesTLV / 2023 | `dockerfile`, `prebuilt_rehost` | `bundled_libc_only` | stack_rop | `single_service` | 9 / 2.0 MiB |
| 50 | `gh-c8994bfe8e2d35da8fa6611b` | `APB` / `fast_track_no_writeup` | `CUHK0x/cuhk-ctf-2024-challenges` / cuhk ctf / 2024 | `dockerfile_compose`, `hybrid` | `static` | format_string, shellcode_seccomp, vm_emulator | `single_service` | 11 / 639.9 KiB |
| 51 | `saj-2024-pwn-adventure` | `AWPB` / `fast_track_full` | `CyberLabs-Infosec/PearlCTF_Challenges_Public_2024` / Pearl / 2024 | `dockerfile`, `hybrid` | `bundled_loader_only` | stack_rop | `single_service` | 10 / 2.4 MiB |
| 52 | `saj-2022-pwn-ringsofsaturn` | `APB` / `fast_track_no_writeup` | `tj-oconnor/spaceheroes_ctf` / SpaceHeroes / 2022 | `dockerfile_compose`, `hybrid` | `bundled_libc_loader` | heap | `multi_service` | 27 / 2.2 MiB |
| 53 | `gh-6ad778ed7e813f9851364036` | `AWPB` / `fast_track_full` | `ret2school/ctf` / imaginaryctf / 2023 | `build_metadata`, `hybrid` | `static` | kernel | `single_service` | 23 / 74.7 MiB |
| 54 | `saj-2024-pwn-format-muscle` | `APB` / `fast_track_no_writeup` | `Thehackerscrew/CrewCTF-2024-Public` / CrewCTF / 2024 | `dockerfile`, `hybrid` | `musl` | other | `single_service` | 6 / 716.7 KiB |
| 55 | `saj-2022-pwn-asianparents` | `AWPB` / `fast_track_full` | `balsn/balsn-ctf-2022` / Balsn / 2022 | `dockerfile_compose`, `hybrid` | `bundled_libc_only` | stack_rop | `single_service` | 15 / 2.5 MiB |
| 56 | `saj-2025-pwn-prospector` | `APB` / `fast_track_no_writeup` | `justcatthefish/justctf-2025` / justCTF / 2025 | `dockerfile`, `hybrid` | `bundled_loader_only` | stack_rop | `single_service` | 16 / 314.4 KiB |
| 57 | `saj-2025-pwn-is-this-web` | `AWPB` / `fast_track_full` | `MadrHacks/snakeCTF2023-Writeups` / snakeCTF / 2025 | `dockerfile_compose`, `hybrid` | `system_libc` | vm_emulator | `single_service` | 13 / 63.9 MiB |
| 58 | `saj-2024-pwn-linker-as-a-service` | `APB` / `fast_track_no_writeup` | `les-amateurs/actf-2024-rctf` / AmateursCTF / 2024 | `dockerfile`, `source_build` | `bundled_loader_only` | other | `single_service` | 24 / 905.4 KiB |
| 59 | `gh-d89e37825609f81e3043c42e` | `AWPB` / `fast_track_full` | `SECCON/Beginners_CTF_2022` / BeginnersCTF / 2022 | `dockerfile_compose`, `hybrid` | `static` | shellcode_seccomp, stack_rop | `single_service` | 20 / 856.7 KiB |
| 60 | `saj-2021-pwn-helpless` | `APB` / `fast_track_no_writeup` | `Crusaders-of-Rust/corCTF-2021-public-challenge-archive` / corCTF / 2021 | `dockerfile_compose`, `prebuilt_rehost` | `bundled_libc_only` | stack_rop | `single_service` | 6 / 19.9 MiB |
| 61 | `gh-6f80658fbf3ea86dafc20c5f` | `AWPB` / `fast_track_full` | `JeanneD-Hack-CTF/JeanneD-Hack-CTF-2026` / JeanneD Hack CTF / 2026 | `dockerfile_compose`, `source_build` | `unknown_or_non_elf` | other | `multi_service` | 45 / 385.1 KiB |
| 62 | `saj-2024-pwn-directory` | `APB` / `fast_track_no_writeup` | `BYU-CSA/BYUCTF-2024` / BYUCTF / 2024 | `dockerfile_compose`, `hybrid` | `system_libc` | other | `single_service` | 9 / 22.8 KiB |
| 63 | `saj-2025-pwn-haatetepe` | `AWPB` / `fast_track_full` | `Norske-Nokkelsnikere/nns-ctf-2025` / NNS / 2025 | `dockerfile`, `hybrid` | `static` | stack_rop | `single_service` | 9 / 890.9 KiB |
| 64 | `saj-2021-pwn-coffeeshop` | `APB` / `fast_track_no_writeup` | `idekctf/idekctf-2021` / idekCTF / 2021 | `dockerfile`, `hybrid` | `bundled_libc_loader` | heap | `single_service` | 15 / 2.2 MiB |
| 65 | `saj-2020-na-skywriting` | `AWPB` / `fast_track_full` | `redpwn/redpwnctf-2021-challenges` / redpwn / 2020 | `dockerfile`, `hybrid` | `bundled_libc_only` | stack_rop | `single_service` | 17 / 2.3 MiB |
| 66 | `saj-2023-pwn-you-want-me-to-run-what` | `APB` / `fast_track_no_writeup` | `UMD-CSEC/UMDCTF-Public-Challenges` / UMDCTF / 2023 | `dockerfile`, `hybrid` | `static` | other | `single_service` | 15 / 8.6 MiB |
| 67 | `gh-cecbb796f52e3898df80d06e` | `AWPB` / `fast_track_full` | `PWrWhiteHats/BtS-CTF-Challenges-03-2021` / BtS CTF 03 / 2021 | `dockerfile`, `hybrid` | `system_libc` | other | `single_service` | 9 / 19.1 KiB |
| 68 | `saj-2022-pwn-warmup2` | `APB` / `fast_track_no_writeup` | `ubcctf/sapling-ctf-2022` / MapleCTF / 2022 | `dockerfile`, `hybrid` | `bundled_libc_only` | format_string, stack_rop | `single_service` | 10 / 3.9 MiB |
| 69 | `saj-2023-pwn-strings` | `AWPB` / `fast_track_full` | `n00bzUnit3d/n00bzCTF2024-Official-Writeups` / n00bzCTF / 2023 | `dockerfile_compose`, `hybrid` | `system_libc` | format_string | `single_service` | 13 / 44.5 KiB |
| 70 | `gh-d7c4052e4b4f5e1bdfb491ff` | `APB` / `fast_track_no_writeup` | `BreizhCTF/breizhctf-2024` / breizhctf / 2024 | `dockerfile_compose`, `source_build` | `unknown_or_non_elf` | stack_rop | `single_service` | 8 / 180.8 KiB |
| 71 | `saj-2025-pwn-heap-of-the-brave` | `AWPB` / `fast_track_full` | `delta/PCTF25-Writeups` / Pragyan / 2025 | `dockerfile_compose`, `hybrid` | `bundled_libc_loader` | heap | `single_service` | 11 / 2.0 MiB |
| 72 | `saj-2024-pwn-where2go` | `APB` / `fast_track_no_writeup` | `ufsit/SwampCTF-2025-Challenges` / SwampCTF / 2024 | `build_metadata`, `hybrid` | `system_libc` | stack_rop | `single_service` | 4 / 15.2 KiB |
| 73 | `gh-ecda0c754e536cafb96812b6` | `AWPB` / `fast_track_full` | `CavemanJay/PicoCTF` / pico ctf / 2022 | `build_metadata`, `source_build` | `unknown_or_non_elf` | shellcode_seccomp | `single_service` | 24 / 8.2 MiB |
| 74 | `saj-2025-pwn-heapie-2` | `APB` / `fast_track_no_writeup` | `CrateOrg/crate-ctf` / CrateCTF / 2025 | `dockerfile_compose`, `hybrid` | `static` | heap | `single_service` | 9 / 760.9 KiB |
| 75 | `gh-cbaaa754ed2e2122d2b51b00` | `AWPB` / `fast_track_full` | `redpwn/redpwnctf-2019-challenges` / redpwnctf / 2019 | `dockerfile`, `hybrid` | `system_libc` | shellcode_seccomp, stack_rop | `single_service` | 11 / 27.2 KiB |
| 76 | `gh-a98554e0613cbd503e87d10b` | `APB` / `fast_track_no_writeup` | `min-yang/CTF-Challenge-Collection` / WaniCTF / 2023 | `build_metadata`, `source_build` | `unknown_or_non_elf` | other | `single_service` | 3 / 2.3 KiB |
| 77 | `gh-e01f4b11a572699f3695620b` | `AWPB` / `fast_track_full` | `nobodyisnobody/write-ups` / Blackhat MEA CTF / 2023 | `dockerfile_compose`, `hybrid` | `bundled_libc_loader` | other | `single_service` | 14 / 6.8 MiB |
| 78 | `gh-6cb1ca15dc12bb57d1e8f954` | `APB` / `fast_track_no_writeup` | `Heroes-Cyber-Security/2023-hcs-intersec-ctf` / hcs intersec ctf / 2023 | `dockerfile`, `hybrid` | `system_libc` | other | `single_service` | 8 / 20.7 KiB |
| 79 | `gh-35cbfd8fcff12adf3fa3717a` | `AWPB` / `fast_track_full` | `ItemizeNTNU/kid20-challenges` / kid20 / 2020 | `dockerfile_compose`, `hybrid` | `system_libc` | other | `single_service` | 14 / 223.7 KiB |
| 80 | `gh-617f8961bbd57146ec3859e1` | `APB` / `fast_track_no_writeup` | `kyfuse/ctf-archive` / MetaCTF / 2021 | `dockerfile`, `source_build` | `bundled_libc_only` | stack_rop | `single_service` | 17 / 39.8 MiB |
| 81 | `gh-678b0776161cb8ba38b0ddfe` | `AWPB` / `fast_track_full` | `LJP-TW/CTF` / CTFZone / 2019 | `build_metadata`, `hybrid` | `system_libc` | shellcode_seccomp, stack_rop | `single_service` | 16 / 2.6 MiB |
| 82 | `gh-e871aaabc0ad739c25a49d08` | `APB` / `fast_track_no_writeup` | `uclaacm/lactf-archive` / lactf / 2024 | `dockerfile`, `hybrid` | `bundled_libc_loader` | heap | `single_service` | 8 / 2.2 MiB |
| 83 | `gh-cce6b5576aab2d5292ff0cb1` | `AWPB` / `fast_track_full` | `Shellmates/MicroCTF-2021-Finals-challs-` / MicroCTF / 2021 | `dockerfile_compose`, `hybrid` | `system_libc` | shellcode_seccomp | `single_service` | 9 / 60.8 KiB |
| 84 | `gh-ff978fd75c915bd5489fc5db` | `APB` / `fast_track_no_writeup` | `AirOverflow/PCC-Challs-Public` / PCC / 2023 | `dockerfile`, `hybrid` | `system_libc` | stack_rop | `single_service` | 10 / 22.5 KiB |
| 85 | `saj-2023-pwn-not-malloc` | `AWPB` / `fast_track_full` | `polygl0ts/lakectf-22-23-public` / LakeCTF / 2023 | `dockerfile`, `hybrid` | `bundled_libc_loader` | heap, stack_rop | `single_service` | 15 / 8.7 MiB |
| 86 | `gh-8b033e13b216f7d1fc9da775` | `APB` / `fast_track_no_writeup` | `404GH0ST/CTF-Journey` / c2c / 2026 | `dockerfile`, `hybrid` | `bundled_libc_only` | heap | `single_service` | 14 / 3.2 MiB |
| 87 | `saj-2023-pwn-flight` | `AWPB` / `fast_track_full` | `BSidesSF/ctf-2023-release` / BSidesSF / 2023 | `dockerfile`, `hybrid` | `system_libc` | other | `single_service` | 9 / 51.1 KiB |
| 88 | `gh-c04dcf77cc7aa15234389efb` | `APB` / `fast_track_no_writeup` | `harshulvijay/BITSkrieg-InductionCTF-2025` / BITSkrieg InductionCTF / 2025 | `dockerfile`, `source_build` | `unknown_or_non_elf` | other | `single_service` | 4 / 2.2 KiB |
| 89 | `saj-2026-pwn-basalt-chamber` | `AWPB` / `fast_track_full` | `0xlast500-0xV01D/0xV01D-CTF` / 0xV01D / 2026 | `dockerfile`, `hybrid` | `static` | shellcode_seccomp | `single_service` | 9 / 702.4 KiB |
| 90 | `gh-6693bed7813ad54b06193d00` | `APB` / `fast_track_no_writeup` | `bmleeBigby/cscctf` / cscctf / 2019 | `dockerfile_compose`, `source_build` | `bundled_libc_only` | shellcode_seccomp | `single_service` | 9 / 1.9 MiB |
| 91 | `gh-2f68232a08e0468a2f79d392` | `AWPB` / `fast_track_full` | `silentzero192/CTFtime-Writeups` / 0xvoidCTF / 2026 | `dockerfile`, `hybrid` | `static` | shellcode_seccomp | `single_service` | 8 / 712.3 KiB |
| 92 | `gh-446daaef67eaba77fdcfc088` | `APB` / `fast_track_no_writeup` | `osirislab/CSAW-CTF-2023-Quals` / CSAW CTF / 2023 | `dockerfile`, `source_build` | `unknown_or_non_elf` | other | `single_service` | 7 / 2.0 KiB |
| 93 | `saj-2024-pwn-bytecode` | `AWPB` / `fast_track_full` | `Akasec-1337/Akasec-CTF-2024` / Akasec / 2024 | `dockerfile`, `hybrid` | `bundled_libc_loader` | heap, shellcode_seccomp, vm_emulator | `single_service` | 18 / 2.6 MiB |
| 94 | `gh-86e6f6e031779e125dce97a3` | `APB` / `fast_track_no_writeup` | `infosec-ucalgary/magpieCTF2022-public` / magpieCTF / 2022 | `dockerfile`, `hybrid` | `system_libc` | other | `single_service` | 8 / 38.2 KiB |
| 95 | `saj-2023-pwn-champions-heap` | `AWPB` / `fast_track_full` | `Shellmates/BSides-Algiers-2025-challenges` / BSidesAlgiers / 2023 | `dockerfile_compose`, `hybrid` | `bundled_libc_loader` | heap, shellcode_seccomp, stack_rop | `single_service` | 12 / 17.4 MiB |
| 96 | `gh-91b6f2c11338e3f2bde7f926` | `APB` / `fast_track_no_writeup` | `securinets-insat/Friendly-CTF-2024` / Friendly CTF / 2024 | `dockerfile_compose`, `hybrid` | `system_libc` | stack_rop | `single_service` | 6 / 20.5 KiB |
| 97 | `gh-69a56364382cede9b3074e69` | `AWPB` / `fast_track_full` | `polycyber/PolyPwnCTF-2025-Challenges` / PolyPwnCTF / 2025 | `dockerfile`, `source_build` | `unknown_or_non_elf` | shellcode_seccomp | `single_service` | 16 / 6.9 MiB |
| 98 | `gh-d0f6a02821b09bf650b0de62` | `APB` / `fast_track_no_writeup` | `NUSGreyhats/welcome-ctf-2023-public` / welcome ctf / 2023 | `dockerfile_compose`, `hybrid` | `system_libc` | other | `single_service` | 6 / 19.1 KiB |
| 99 | `gh-a118f52e8c160dc35e81533c` | `AWPB` / `fast_track_full` | `Shellmates/Hack-Till-Shour-2k22-CTF-challs` / Hack Till Shour 2k22 CTF / 2022 | `dockerfile_compose`, `hybrid` | `system_libc` | other | `single_service` | 9 / 19.3 KiB |
| 100 | `saj-2024-pwn-free-free-free` | `APB` / `fast_track_no_writeup` | `SECCON/SECCON_Beginners_CTF_2024` / SECCON / 2024 | `dockerfile_compose`, `hybrid` | `system_libc` | heap, stack_rop | `single_service` | 6 / 29.0 KiB |

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

### 31. `gh-a413f013eb02fb618a538106` — stdvec

- Identity: tsgctf / 2020 / Pwn
- Source: `tsg-ut/tsgctf2020`; `https://github.com/tsg-ut/tsgctf2020/tree/beb090fd5178e6f2ff6fb202fb17f51d345bb5a3/pwn/stdvec`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `bundled_libc_only`; `heap`
- Selection reason: adds event tsgctf; adds source tsg-ut/tsgctf2020
- Material fingerprint: `294b43d9fe9d3f5ebaebdfceddb68526360447b2d8d3b0598b118088e9a2db98`
- Material paths:
  - A (10):
    - `materials/attachments/lib.cpp` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/public/lib.cpp` (`1b110170bee4b926df41dfb3a5a5395c051d50ab531cd71e621a0e5cab556ea5`, 7554 bytes)
    - `materials/attachments/package/libc.so.6` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/public/package/libc.so.6` (`f0ad9639b2530741046e06c96270b25da2339b6c15a7ae46de8fb021b3c4f529`, 2030544 bytes)
    - `materials/attachments/package/python3.7` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/public/package/python3.7` (`da7d2bd6e5219a98d39c792051f74f14e8c398ac0e773a5fc697e4907ef43e6a`, 4873376 bytes)
    - `materials/attachments/package/run.py` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/public/package/run.py` (`d0494d2f0ee33ad98d94fd960719a05aef6a1a89b38c9936d9436c6a87cb2ca2`, 1485 bytes)
    - `materials/attachments/package/sample.py` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/public/package/sample.py` (`db995a471925781c6599b76fd6aff1116d42103b1598c9c7fd2b945baacaa1f1`, 187 bytes)
    - `materials/attachments/package/stdvec.cpython-37m-x86_64-linux-gnu.so` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/public/package/stdvec.cpython-37m-x86_64-linux-gnu.so` (`b357e2a9423601788501815e050d35f17c85fe217068f35af17b368b658d2c06`, 86104 bytes)
    - `materials/attachments/package/template.py` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/public/package/template.py` (`6590c4823a5ca57814e636f490218edd5d75fb7b42980417dafb96f6ea48007a`, 265 bytes)
    - `materials/attachments/proof-of-work.py` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/public/proof-of-work.py` (`e4736d797aab11282aeef5e10830938d2038aa873e12c00ebac5f19bee185372`, 765 bytes)
    - `materials/attachments/run.py` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/public/run.py` (`9c96e58076383cf555c6f1c5c647b20cddb3bae2a58a604c216a3ec61487dcb8`, 1197 bytes)
    - `materials/attachments/setup.py` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/public/setup.py` (`3feeaa45dc160a0743dec0f5dd810054564fa18ed45b80a446dfd93afa407dd5`, 162 bytes)
  - W (2):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/writeups/README.md` (`b9e8e58dae7c8f002f08a2671c189be757e2b579412eb402e04a42fcde09f539`, 6571 bytes)
    - `materials/writeups/writeup.md` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/writeups/writeup.md` (`0062831c42a5294fc98cedd21c8b838927f7e935a03142d12f04a07d3569f015`, 3054 bytes)
  - P (2):
    - `materials/exploit/exploit.py` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/solve/exploit.py` (`ccfbeac191db6366f9f7e606c3740233c83ad722038226c167586ae04cd98b28`, 1223 bytes)
    - `materials/exploit/solver/solve.py` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/solve/solver/solve.py` (`d22cab58f8086f816acac8cd89de1d59885e441244c541d8bc88348fd80c7a84`, 1555 bytes)
  - B (10):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/build/Dockerfile` (`d0e02b7f64209519097d89ec51a01fc0d20955c0af7ed12dd92d301b78423e62`, 702 bytes)
    - `materials/deployment/build/env/run.py` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/build/build/env/run.py` (`d0494d2f0ee33ad98d94fd960719a05aef6a1a89b38c9936d9436c6a87cb2ca2`, 1485 bytes)
    - `materials/deployment/build/env/run.sh` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/build/build/env/run.sh` (`87c874f67627510040df1632de216b20f5ab46e3818bfdb92e7cb9598f6bed48`, 49 bytes)
    - `materials/deployment/build/env/template.py` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/build/build/env/template.py` (`6590c4823a5ca57814e636f490218edd5d75fb7b42980417dafb96f6ea48007a`, 265 bytes)
    - `materials/deployment/build/proof-of-work.py` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/build/build/proof-of-work.py` (`e4736d797aab11282aeef5e10830938d2038aa873e12c00ebac5f19bee185372`, 765 bytes)
    - `materials/deployment/build/start.sh` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/build/build/start.sh` (`c3a48a55b7f2982c2cd4a41d06f6063eebdf90dfeb77c3523dc74250a3234b06`, 213 bytes)
    - `materials/deployment/dist/package/sample.py` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/build/dist/package/sample.py` (`db995a471925781c6599b76fd6aff1116d42103b1598c9c7fd2b945baacaa1f1`, 187 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/build/docker-compose.yml` (`53aaecc14175bbfc3fdf0af07115166d9a914064980acdf4c162a32ec1b1fc23`, 553 bytes)
    - `materials/deployment/src/lib.cpp` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/build/src/lib.cpp` (`1b110170bee4b926df41dfb3a5a5395c051d50ab531cd71e621a0e5cab556ea5`, 7554 bytes)
    - `materials/deployment/src/setup.py` ← `work/materials/pwn-v11/gh-a413f013eb02fb618a538106/build/src/setup.py` (`3feeaa45dc160a0743dec0f5dd810054564fa18ed45b80a446dfd93afa407dd5`, 162 bytes)

### 32. `gh-c4c32267c212dedfa844cff2` — bitflips files

- Identity: 0xfun26 / 2026 / Pwn
- Source: `0xStraw-Hat/pwn-challenges`; `https://github.com/0xStraw-Hat/pwn-challenges/tree/70bd564b4f1d4dc2f34f02e0b3045f1a51d144eb/0xfun26/pwn/bitflips_files`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `nonstandard`; `bundled_libc_loader`; `other`
- Selection reason: adds event 0xfun26; adds source 0xStraw-Hat/pwn-challenges
- Material fingerprint: `6578e939157e5cd31b1e8dbf189a1d81dcc1ca858e255bfae8e374ea66014b59`
- Material paths:
  - A (2):
    - `materials/attachments/ld-linux-x86-64.so.2` ← `work/materials/pwn-v11/gh-c4c32267c212dedfa844cff2/public/ld-linux-x86-64.so.2` (`e8bd4332b33dd698f608519d0c93f10846925202e82ead22779778ad112bbc4a`, 246760 bytes)
    - `materials/attachments/libc.so.6` ← `work/materials/pwn-v11/gh-c4c32267c212dedfa844cff2/public/libc.so.6` (`d160b7ae4621987092cb730aef3c8bc0ba3076a4d9dd40ee3e14570121412e3c`, 2145632 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/gh-c4c32267c212dedfa844cff2/solve/solve.py` (`26f0c8e59e5e62255d71cbb0bcf07b8cc3a8d8dc5e78e2cd23898cd382e70a93`, 3072 bytes)
  - B (1):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-c4c32267c212dedfa844cff2/build/Dockerfile` (`9811b31401df3fbdeda85f80c809692ff9a9d3360eed3204e6fa0b9014104363`, 437 bytes)

### 33. `saj-2025-pwn-nitebus` — NiteBus

- Identity: niteCTF / 2025 / Pwn
- Source: `Cryptonite-MIT/niteCTF-2025`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/niteCTF/2025/pwn/NiteBus`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile`; `prebuilt_rehost`; `static`; `format_string`, `shellcode_seccomp`, `vm_emulator`
- Selection reason: adds event niteCTF; adds source Cryptonite-MIT/niteCTF-2025
- Material fingerprint: `1c85e897aec74a56e40af460d5cde391988050f9ec8332cf0aeabe021367ae86`
- Material paths:
  - A (1):
    - `materials/attachments/nitebus` ← `work/materials/pwn-v11/saj-2025-pwn-nitebus/public/nitebus` (`6469b6f92f95e9920978d53de76fd73f0053bf27bd789501f7338fc42778dfac`, 813408 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2025-pwn-nitebus/writeups/README.md` (`a469d194eed21fcb287f53ed4f202f35db0ab993f916398ab334309647e4a0b4`, 815 bytes)
  - P (3):
    - `materials/exploit/solution/solve.py` ← `work/materials/pwn-v11/saj-2025-pwn-nitebus/solve/solution/solve.py` (`31a6ce68e081f1a6abeb842db2af1a6584fe748fad449c5f9a12290a61f77ec1`, 2108 bytes)
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2025-pwn-nitebus/solve/solve.py` (`cf191e2a9842bfc9217c1e8644311a16c9031732c17687c06a8e044c2069919a`, 4443 bytes)
    - `materials/exploit/solve_unintended.py` ← `work/materials/pwn-v11/saj-2025-pwn-nitebus/solve/solve_unintended.py` (`5614c51050d5a6468bdf4b5c3009feb18c8f1c8e7db601affb879b511193107e`, 1821 bytes)
  - B (1):
    - `materials/deployment/challenge/Dockerfile` ← `work/materials/pwn-v11/saj-2025-pwn-nitebus/build/challenge/Dockerfile` (`97d37b6ec5bf29d66d187cafc9637e5bcf8cfd8fd2560006122997e9d43418be`, 369 bytes)

### 34. `saj-2025-pwn-canon-event` — Canon_Event

- Identity: TRX / 2025 / Pwn
- Source: `TheRomanXpl0it/TRX-CTF-2025`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/TRX/2025/pwn/Canon_Event`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `compose`; `hybrid`; `bundled_libc_loader`; `shellcode_seccomp`
- Selection reason: adds event TRX; adds source TheRomanXpl0it/TRX-CTF-2025
- Material fingerprint: `a83baff18564df3dcdf30bd4cd79b833bbec5963adeaff5f625cc35cd68f20a7`
- Material paths:
  - A (4):
    - `materials/attachments/chall.c` ← `work/materials/pwn-v11/saj-2025-pwn-canon-event/public/chall.c` (`1ede008b82dd613298949519c7a767aad6559be8092503ea7f0593ebb38e9e52`, 3184 bytes)
    - `materials/attachments/dist/chall` ← `work/materials/pwn-v11/saj-2025-pwn-canon-event/public/dist/chall` (`022caf7946ffcc6645b349d557d6729202148eb1595cf533c5c053837436b1ed`, 22736 bytes)
    - `materials/attachments/dist/glibc/ld-linux-x86-64.so.2` ← `work/materials/pwn-v11/saj-2025-pwn-canon-event/public/dist/glibc/ld-linux-x86-64.so.2` (`db4dfc56d13ebb4d3c49c7c0309c030e73ebee1d36b944359de2ea0d1eac1c4b`, 915800 bytes)
    - `materials/attachments/dist/glibc/libc.so.6` ← `work/materials/pwn-v11/saj-2025-pwn-canon-event/public/dist/glibc/libc.so.6` (`7dbcc4680470768c7b62aab49fbddee2634127ab771659e4b0cdd360147bab78`, 2449104 bytes)
  - W: absent
  - P (2):
    - `materials/exploit/private/poc.c` ← `work/materials/pwn-v11/saj-2025-pwn-canon-event/solve/private/poc.c` (`92376dc6b62ffb2d46b5cf3502fc854860e146c79b9e6303935fa08ce68da80a`, 3345 bytes)
    - `materials/exploit/private/solve.py` ← `work/materials/pwn-v11/saj-2025-pwn-canon-event/solve/private/solve.py` (`e5eae82515ea36e7bad4086bce46e7ba8d6cb7cb20819ab57a5002ca3aa367df`, 4353 bytes)
  - B (4):
    - `materials/deployment/private/Makefile` ← `work/materials/pwn-v11/saj-2025-pwn-canon-event/build/private/Makefile` (`ff796729cc1cd904eb11b9e2343cceeb094876b8df3c46a40a1f3650bfcd08b8`, 117 bytes)
    - `materials/deployment/private/compose.yml` ← `work/materials/pwn-v11/saj-2025-pwn-canon-event/build/private/compose.yml` (`5540cc35e98ede4d4ee2b269bdf5ce077e8843d357fcd4018c0731f8183708f6`, 539 bytes)
    - `materials/deployment/remote/chall.c` ← `work/materials/pwn-v11/saj-2025-pwn-canon-event/build/remote/chall.c` (`1ede008b82dd613298949519c7a767aad6559be8092503ea7f0593ebb38e9e52`, 3184 bytes)
    - `materials/deployment/remote/compose.yml` ← `work/materials/pwn-v11/saj-2025-pwn-canon-event/build/remote/compose.yml` (`b68175c6a0ae69e0858a2725c966db98e43818a29821177fd024405a4ee06144`, 666 bytes)

### 35. `saj-2020-pwn-guessinggame2` — GuessingGame2

- Identity: picoCTF / 2020 / Pwn
- Source: `picoCTF/picoCTF`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/picoCTF/2020/pwn/GuessingGame2`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `build_metadata`; `hybrid`; `bundled_loader_only`; `format_string`, `stack_rop`
- Selection reason: adds event picoCTF; adds source picoCTF/picoCTF
- Material fingerprint: `f612ce77644db535e271405a5ce4d6168c544420ca407870150261bbbcc1ca70`
- Material paths:
  - A (6):
    - `materials/attachments/ld-2.27.so` ← `work/materials/pwn-v11/saj-2020-pwn-guessinggame2/public/ld-2.27.so` (`1fc1915af2295ce24f359f8f6c6dcf50560a60f9d338e00ea5ebd7b71e95e90b`, 159956 bytes)
    - `materials/attachments/libc6-i386_2.27-3ubuntu1.5_amd64.so` ← `work/materials/pwn-v11/saj-2020-pwn-guessinggame2/public/libc6-i386_2.27-3ubuntu1.5_amd64.so` (`01e0ffcd6333d1f86f1a03ec449623fa53a8540521bb15e33fe0e911f3c15886`, 1926828 bytes)
    - `materials/attachments/libc6-i386_2.27-3ubuntu1.6_amd64.so` ← `work/materials/pwn-v11/saj-2020-pwn-guessinggame2/public/libc6-i386_2.27-3ubuntu1.6_amd64.so` (`34fa53bf0cd1dd33a75f241ea43cf630a7c23c9a78d4af04debc3b2d81e1d122`, 1926828 bytes)
    - `materials/attachments/libc6_2.37-0ubuntu2_i386.so` ← `work/materials/pwn-v11/saj-2020-pwn-guessinggame2/public/libc6_2.37-0ubuntu2_i386.so` (`58345923b395505359a3db7a106e523b44c95feda81509f13fd719d01ff4bf4e`, 2276528 bytes)
    - `materials/attachments/vuln` ← `work/materials/pwn-v11/saj-2020-pwn-guessinggame2/public/vuln` (`4e9c3d4cc1c0db2a4a3b84080276f245ed389d3b78b8ab79fe72c765e0dc5c28`, 7592 bytes)
    - `materials/attachments/vuln.c` ← `work/materials/pwn-v11/saj-2020-pwn-guessinggame2/public/vuln.c` (`0b40230b9cdac08d2bf1ae9bf811ae4bc7746c037ad969d6fd31ee5c68dbdf9b`, 1156 bytes)
  - W (1):
    - `materials/writeups/guessing-game-2-solution-picoctf-2020-mini-competition-writeup-picoctf-solutions.html` ← `work/materials/pwn-v11/saj-2020-pwn-guessinggame2/writeups/guessing-game-2-solution-picoctf-2020-mini-competition-writeup-picoctf-solutions.html` (`1a84461b2720592fa0489f323e2e8e38cf5b578b65cd6cb68d9ee3420562e72b`, 168065 bytes)
  - P (1):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2020-pwn-guessinggame2/solve/solve.py` (`0c4dddbeab3707d130c2be7e0e3f37f227e2360d5e213a139af9e6c907cb96c7`, 3640 bytes)
  - B (1):
    - `materials/deployment/Makefile` ← `work/materials/pwn-v11/saj-2020-pwn-guessinggame2/build/Makefile` (`8c6e28e678a763a0c1f639ccf3fb9d984a7b4f733448b759d58ab6fc02cdb1b6`, 74 bytes)

### 36. `saj-2024-pwn-faulty-kernel` — Faulty_Kernel

- Identity: DownUnderCTF / 2024 / Pwn
- Source: `DownUnderCTF/Challenges_2024_Public`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/DownUnderCTF/2024/pwn/Faulty_Kernel`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile_compose`; `source_build`; `musl`; `kernel`
- Selection reason: adds event DownUnderCTF; adds source DownUnderCTF/Challenges_2024_Public
- Material fingerprint: `c71321f42596b7f7e90b85a23fb237a5c082b31447832d2232fa44d342164436`
- Material paths:
  - A (4):
    - `materials/attachments/bzImage` ← `work/materials/pwn-v11/saj-2024-pwn-faulty-kernel/public/bzImage` (`5e6872f7ca65f74c7d9f39de867e517aa8c483f8067adf70b22877de28dea6c5`, 13267968 bytes)
    - `materials/attachments/ctfcli.yaml` ← `work/materials/pwn-v11/saj-2024-pwn-faulty-kernel/public/ctfcli.yaml` (`b77054ecb12ecc1f04477a05fd360f23fadd82dc77ada097a48f2a6eb5e501cf`, 378 bytes)
    - `materials/attachments/rootfs.cpio` ← `work/materials/pwn-v11/saj-2024-pwn-faulty-kernel/public/rootfs.cpio` (`df7bc498842e8e7b28f7a5e7cbcb6f56f7b8eaf93923097908d2b7eddd0ee1e8`, 5010944 bytes)
    - `materials/attachments/src.c` ← `work/materials/pwn-v11/saj-2024-pwn-faulty-kernel/public/src.c` (`27873d1cf3c3945d3e5479b6b8890a29dcbf19582cb2ffc55164dbd3a730e9cd`, 2779 bytes)
  - W: absent
  - P (4):
    - `materials/exploit/solve/exploit` ← `work/materials/pwn-v11/saj-2024-pwn-faulty-kernel/solve/solve/exploit` (`6e885b74a176c46593ed594d291145e87f3570e3f89fb9b3eb3947c150672068`, 920016 bytes)
    - `materials/exploit/solve/exploit-musl` ← `work/materials/pwn-v11/saj-2024-pwn-faulty-kernel/solve/solve/exploit-musl` (`5d52333e037a96c0fe8e1a335f3b0ee0faef2e4d0f0a2c8a2247123635c9bdc3`, 45520 bytes)
    - `materials/exploit/solve/exploit.c` ← `work/materials/pwn-v11/saj-2024-pwn-faulty-kernel/solve/solve/exploit.c` (`1617cd46c28b3e7b6b1639cab56bd31886b2749a0a4ddcec3e99d19776dea72e`, 3502 bytes)
    - `materials/exploit/solve/solve.py` ← `work/materials/pwn-v11/saj-2024-pwn-faulty-kernel/solve/solve/solve.py` (`bdaeb223a249fe57c80f6796ca1d8d1a67e7d71d778fb5f0ac3ca2ad555e34c2`, 751 bytes)
  - B (4):
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/saj-2024-pwn-faulty-kernel/build/docker-compose.yml` (`bbef1ba7474924558dd50c83c704b1242b038cba258b2e143548160df8902597`, 123 bytes)
    - `materials/deployment/src/Dockerfile` ← `work/materials/pwn-v11/saj-2024-pwn-faulty-kernel/build/src/Dockerfile` (`40b3fe89ab7fb2e08a1745a36ab0d4bc555c73b97644f7c270a102353a665731`, 376 bytes)
    - `materials/deployment/src/run.sh` ← `work/materials/pwn-v11/saj-2024-pwn-faulty-kernel/build/src/run.sh` (`240572f20b70ebe99b390f166211c2b0db211e8a4c1e9dc0a21fb5e0c6070218`, 245 bytes)
    - `materials/deployment/src/src.c` ← `work/materials/pwn-v11/saj-2024-pwn-faulty-kernel/build/src/src.c` (`27873d1cf3c3945d3e5479b6b8890a29dcbf19582cb2ffc55164dbd3a730e9cd`, 2779 bytes)

### 37. `gh-1b722a3400c6597cac56e5c9` — gibson

- Identity: cyber open / 2022 / Pwn
- Source: `tj-oconnor/cyber-open-2022`; `https://github.com/tj-oconnor/cyber-open-2022/tree/b4328c7f05c8d5e2b3a140e873b3a65bf3c8beaa/pwn/gibson`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `bundled_libc_only`; `stack_rop`
- Selection reason: adds event cyber open; adds source tj-oconnor/cyber-open-2022
- Material fingerprint: `fa7def7fab99bc25017f358d7ae95fc2ed0f3a667137afa230ab21f7887fa413`
- Material paths:
  - A (8):
    - `materials/attachments/gibson_s390x/bin/libc.so.6` ← `work/materials/pwn-v11/gh-1b722a3400c6597cac56e5c9/public/gibson_s390x/bin/libc.so.6` (`94e77739dcdae39e4eff7e2aa8e5170abbf640de5a8a79e711f8131de119e3b4`, 1906880 bytes)
    - `materials/attachments/gibson_s390x/bin/mainframe` ← `work/materials/pwn-v11/gh-1b722a3400c6597cac56e5c9/public/gibson_s390x/bin/mainframe` (`5f9b46ab57ea35f4773b335380a910c0562d6ac170b69cd7bb72fede5bc4cb98`, 8728 bytes)
    - `materials/attachments/gibson_s390x/docs/tips.md` ← `work/materials/pwn-v11/gh-1b722a3400c6597cac56e5c9/public/gibson_s390x/docs/tips.md` (`bc64c87f10750dab041f07abaad616931fed16dcda1d56c8951d99d132d1ce08`, 2942 bytes)
    - `materials/attachments/gibson_s390x/wrapper_scripts/competitor_wrapper.sh` ← `work/materials/pwn-v11/gh-1b722a3400c6597cac56e5c9/public/gibson_s390x/wrapper_scripts/competitor_wrapper.sh` (`44d230d436a363667a315f0e8e678cb3dd2b8773158bda35695a3ed616c7eb91`, 98 bytes)
    - `materials/attachments/gibson_s390x/wrapper_scripts/infrastructure_wrapper.sh` ← `work/materials/pwn-v11/gh-1b722a3400c6597cac56e5c9/public/gibson_s390x/wrapper_scripts/infrastructure_wrapper.sh` (`b6d908cbe41041ab69496d60a77d92b6bfcedfcc806142506ade04bd0319423d`, 101 bytes)
    - `materials/attachments/gibson_s390x/xinetd/competitor.xinetd` ← `work/materials/pwn-v11/gh-1b722a3400c6597cac56e5c9/public/gibson_s390x/xinetd/competitor.xinetd` (`af87296f27de5e8b8f9f2d0365f987db4d407224648e76651debf25fa5b500b3`, 405 bytes)
    - `materials/attachments/gibson_s390x/xinetd/infrastructure.xinetd` ← `work/materials/pwn-v11/gh-1b722a3400c6597cac56e5c9/public/gibson_s390x/xinetd/infrastructure.xinetd` (`a955db535b7844cb4da7d52060f4d0afb68ad4c1c3c6ac6cf62c0b1fe27e8a62`, 409 bytes)
    - `materials/attachments/mainframe.c` ← `work/materials/pwn-v11/gh-1b722a3400c6597cac56e5c9/public/mainframe.c` (`e9f5096d9c3c2dfb3f2d92d630968e9913e23ea5ef906b439fa11662daac6426`, 947 bytes)
  - W (2):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/gh-1b722a3400c6597cac56e5c9/writeups/README.md` (`fa796a8c2b0becb0bb6afca368ff48e3b8b917bfc80657ad1a3588e3f56ce9b3`, 18588 bytes)
    - `materials/writeups/writeup.md` ← `work/materials/pwn-v11/gh-1b722a3400c6597cac56e5c9/writeups/writeup.md` (`709b5438e3819cf4636d682cb1478b6e64910aa93a797c5b718203c44d2d745a`, 3231 bytes)
  - P (2):
    - `materials/exploit/solution.py` ← `work/materials/pwn-v11/gh-1b722a3400c6597cac56e5c9/solve/solution.py` (`f0a8e184b27765f9c42b8f5191f99a875832d05ec41731c1788d312ea3094d05`, 1966 bytes)
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/gh-1b722a3400c6597cac56e5c9/solve/solve.py` (`23baa53b2719638e33bc775c20d39a6604717a2034e1411f7231c85bd1a9c18b`, 788 bytes)
  - B (7):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-1b722a3400c6597cac56e5c9/build/Dockerfile` (`005e86230a1677159541eb3d4e4f848307fc597d8f7b176be9249da3788fe0c9`, 1477 bytes)
    - `materials/deployment/Makefile` ← `work/materials/pwn-v11/gh-1b722a3400c6597cac56e5c9/build/Makefile` (`6363d084c6ce5610b045278c2e6821d1d22fc2e130fb48f5b778acde45b5a436`, 1032 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/gh-1b722a3400c6597cac56e5c9/build/docker-compose.yml` (`836bba1672b375ea22092f465f7459052df38ab50efd4b4bdf1b6898f307cb57`, 453 bytes)
    - `materials/deployment/mainframe.c` ← `work/materials/pwn-v11/gh-1b722a3400c6597cac56e5c9/build/mainframe.c` (`e9f5096d9c3c2dfb3f2d92d630968e9913e23ea5ef906b439fa11662daac6426`, 947 bytes)
    - `materials/deployment/solution.py` ← `work/materials/pwn-v11/gh-1b722a3400c6597cac56e5c9/build/solution.py` (`f0a8e184b27765f9c42b8f5191f99a875832d05ec41731c1788d312ea3094d05`, 1966 bytes)
    - `materials/deployment/wrapper_scripts/competitor_wrapper.sh` ← `work/materials/pwn-v11/gh-1b722a3400c6597cac56e5c9/build/wrapper_scripts/competitor_wrapper.sh` (`44d230d436a363667a315f0e8e678cb3dd2b8773158bda35695a3ed616c7eb91`, 98 bytes)
    - `materials/deployment/wrapper_scripts/infrastructure_wrapper.sh` ← `work/materials/pwn-v11/gh-1b722a3400c6597cac56e5c9/build/wrapper_scripts/infrastructure_wrapper.sh` (`b6d908cbe41041ab69496d60a77d92b6bfcedfcc806142506ade04bd0319423d`, 101 bytes)

### 38. `gh-270f15f0791a91b244cdffc1` — Calc

- Identity: b / 2025 / Pwn
- Source: `koromaki88/ctf-archive`; `https://github.com/koromaki88/ctf-archive/tree/bf02aa77967ac950929a71dd94373f6f87d5c2fd/cscv2025/final-b/pwn/Calc`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `nonstandard`; `unknown_or_non_elf`; `other`
- Selection reason: adds event b; adds source koromaki88/ctf-archive
- Material fingerprint: `cf85139397bf96b3b5a4d39344a77e74e2e2d84194b92a9a51ba3fa6e954c49d`
- Material paths:
  - A (1):
    - `materials/attachments/description.txt` ← `work/materials/pwn-v11/gh-270f15f0791a91b244cdffc1/public/description.txt` (`483923a7110d0f360858a40c434aa008d57bc0b62bdb264ee55ba87e5c2f966e`, 989 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/gh-270f15f0791a91b244cdffc1/solve/solve.py` (`805a561d0a867e6192dbce3b951f7ad951764d5e88c6e290c45e08ea3f522ce4`, 1250 bytes)
  - B (1):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-270f15f0791a91b244cdffc1/build/Dockerfile` (`9ee5c919de42b6e63a94785e3020214d5fe5c492e99058474bd1a5c1ba61f104`, 302 bytes)

### 39. `saj-2024-pwn-drone-adventure` — Drone_Adventure

- Identity: SunshineCTF / 2024 / Pwn
- Source: `SunshineCTF/SunshineCTF-2022-Public`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/SunshineCTF/2024/pwn/Drone_Adventure`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `build_metadata`; `hybrid`; `bundled_loader_only`; `stack_rop`
- Selection reason: adds event SunshineCTF; adds source SunshineCTF/SunshineCTF-2022-Public
- Material fingerprint: `4c315a4428c9c7d3b4805125ce43a3709cc3997127136561b79a1a5a8381d784`
- Material paths:
  - A (4):
    - `materials/attachments/drone.bin` ← `work/materials/pwn-v11/saj-2024-pwn-drone-adventure/public/drone.bin` (`cabd1e0b12d9a27bccf9760ca3de9c91dbb77304b62708f2e4e8522eed1af339`, 28808 bytes)
    - `materials/attachments/drone.c` ← `work/materials/pwn-v11/saj-2024-pwn-drone-adventure/public/drone.c` (`89c1bf6e25fd48d8f0a1e6b430f9aa5c5a4f556c9fd5cadb5c4e5fd477d76a06`, 18652 bytes)
    - `materials/attachments/ld-2.39.so` ← `work/materials/pwn-v11/saj-2024-pwn-drone-adventure/public/ld-2.39.so` (`b7695da977e205398b33922d61493cc1e436cd2321bb2e54fbdc39b95fabeff7`, 236616 bytes)
    - `materials/attachments/libc6_2.39.so` ← `work/materials/pwn-v11/saj-2024-pwn-drone-adventure/public/libc6_2.39.so` (`be321b2e64c8cdfb59fd9cc2fb6c3945c604be767b45420eb05c038ead0d2bb7`, 6228984 bytes)
  - W (1):
    - `materials/writeups/writeup.md` ← `work/materials/pwn-v11/saj-2024-pwn-drone-adventure/writeups/writeup.md` (`e004995b7d1214517d8ed95e12a0f4920d7f683a375374ff65b383b13b28b965`, 5814 bytes)
  - P (4):
    - `materials/exploit/pwn-armx.py` ← `work/materials/pwn-v11/saj-2024-pwn-drone-adventure/solve/pwn-armx.py` (`0312374da4cac3a56ec7f6106f8145fab66e8b263b0556499d066c0c3e95a88e`, 1760 bytes)
    - `materials/exploit/pwn-brks.py` ← `work/materials/pwn-v11/saj-2024-pwn-drone-adventure/solve/pwn-brks.py` (`c0cd9c8c503b00c1be69e597197dec12ca1922bfe158b352fdbe6c8be74d86fb`, 1809 bytes)
    - `materials/exploit/pwn-camo.py` ← `work/materials/pwn-v11/saj-2024-pwn-drone-adventure/solve/pwn-camo.py` (`981c0ff29b7886383bb95a506e8e0fb4ec3a3e69b5ba1cb1318d9932179fb3de`, 1740 bytes)
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2024-pwn-drone-adventure/solve/solve.py` (`a734f6d212ea035dfb8b5b63f88f6111152fd427b59f1db80d2c42d825e3059d`, 2163 bytes)
  - B (1):
    - `materials/deployment/Makefile` ← `work/materials/pwn-v11/saj-2024-pwn-drone-adventure/build/Makefile` (`c2d2812b42319046752ad4872ab0962d3acfb2c409c2a1d6b5affde194f655a8`, 909 bytes)

### 40. `saj-2021-pwn-house-of-tataru` — house_of_tataru

- Identity: N1CTF / 2021 / Pwn
- Source: `Nu1LCTF/n1ctf-2021`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/N1CTF/2021/pwn/house_of_tataru`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile_compose`; `prebuilt_rehost`; `musl`; `heap`, `stack_rop`
- Selection reason: adds event N1CTF; adds source Nu1LCTF/n1ctf-2021
- Material fingerprint: `00acc877f318aa41d5baab8ba7bb402f7ac2acebecca10548058142bd1ad49cf`
- Material paths:
  - A (2):
    - `materials/attachments/ld-musl-x86_64.so.1` ← `work/materials/pwn-v11/saj-2021-pwn-house-of-tataru/public/ld-musl-x86_64.so.1` (`24d94f794e20f6905ca0b5e392b6e0dcef70d3715710c7364069e31612ee073a`, 735728 bytes)
    - `materials/attachments/pwn` ← `work/materials/pwn-v11/saj-2021-pwn-house-of-tataru/public/pwn` (`3c6d3e3687c8f39aa11de84509dcd4346616fcc33ec08ca89b6b571eecc3893a`, 14096 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/exp.py` ← `work/materials/pwn-v11/saj-2021-pwn-house-of-tataru/solve/exp.py` (`2af19b9e9593190ec8651ad7858272e474ddfd733bbf526871f1a3f5058a7890`, 4684 bytes)
  - B (2):
    - `materials/deployment/deploy/Dockerfile` ← `work/materials/pwn-v11/saj-2021-pwn-house-of-tataru/build/deploy/Dockerfile` (`31b1d5da0a434595029dfe5f4e73cbac5f5953250bb9044634cae8d74213ebfb`, 1057 bytes)
    - `materials/deployment/deploy/docker-compose.yml` ← `work/materials/pwn-v11/saj-2021-pwn-house-of-tataru/build/deploy/docker-compose.yml` (`63b29fe9b8c32a957efc50505a0aca9281b772a0b398dae60607685439498bd7`, 103 bytes)

### 41. `gh-bcbf8e4258381230e5ce1de7` — cpp-bbq

- Identity: greyctf26 / 2026 / Pwn
- Source: `NUSGreyhats/greyctf26-challs-public`; `https://github.com/NUSGreyhats/greyctf26-challs-public/tree/48823817e313df0ed74ba1b24d16e9fe793ab45e/finals/pwn/cpp-bbq`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `system_libc`; `heap`
- Selection reason: adds event greyctf26; adds source NUSGreyhats/greyctf26-challs-public
- Material fingerprint: `4d0105be38e22c6db0258434442e259ce91294ee274a7c6d59563a3ae817c2dd`
- Material paths:
  - A (3):
    - `materials/attachments/chall` ← `work/materials/pwn-v11/gh-bcbf8e4258381230e5ce1de7/public/chall` (`29f8a0ada998e84cc5930c067b66b0771471ac74da90eee332ffffd2db6c634f`, 90656 bytes)
    - `materials/attachments/chall.cpp` ← `work/materials/pwn-v11/gh-bcbf8e4258381230e5ce1de7/public/chall.cpp` (`609f41f8af1898a552691f51f02eb172f88636369d59645cb38dee38cc864f59`, 4719 bytes)
    - `materials/attachments/team_token_proxy.py` ← `work/materials/pwn-v11/gh-bcbf8e4258381230e5ce1de7/public/team_token_proxy.py` (`a4cb7d63cf3ed763d3d191a61aebc946efecaa560533958f8a5cad782c416495`, 7675 bytes)
  - W (2):
    - `materials/writeups/human.md` ← `work/materials/pwn-v11/gh-bcbf8e4258381230e5ce1de7/writeups/human.md` (`a01f1606cf0f2688e09119c3e4212af0d207a0c7f3f2ec0881a360974639ecdd`, 2408 bytes)
    - `materials/writeups/llm.md` ← `work/materials/pwn-v11/gh-bcbf8e4258381230e5ce1de7/writeups/llm.md` (`fc8104a3b87898d66aebe9fd46d5743b44711dc81cd3671151ef55d512ed40c8`, 8928 bytes)
  - P (1):
    - `materials/exploit/solve/exploit.py` ← `work/materials/pwn-v11/gh-bcbf8e4258381230e5ce1de7/solve/solve/exploit.py` (`9b23f2d0a7ebb1967ae6d8603e961aa57dc2b5a2e25c5da2471b8731fc79845e`, 7438 bytes)
  - B (7):
    - `materials/deployment/compose.yml` ← `work/materials/pwn-v11/gh-bcbf8e4258381230e5ce1de7/build/compose.yml` (`7758fad31f88b6d332c7de34f30456865ce26be8d1243ed5070a60781c44d420`, 1367 bytes)
    - `materials/deployment/dist/Dockerfile` ← `work/materials/pwn-v11/gh-bcbf8e4258381230e5ce1de7/build/dist/Dockerfile` (`925c651b86dee5149de717ca9210b3e6e7dba6f86d3398ead97f2e59a6694a65`, 805 bytes)
    - `materials/deployment/dist/Dockerfile.build` ← `work/materials/pwn-v11/gh-bcbf8e4258381230e5ce1de7/build/dist/Dockerfile.build` (`03d42fedbd97fc5129e3d19e49bbd45f708a62a49429b7e49eaf614cae6c7404`, 437 bytes)
    - `materials/deployment/dist/chall.cpp` ← `work/materials/pwn-v11/gh-bcbf8e4258381230e5ce1de7/build/dist/chall.cpp` (`609f41f8af1898a552691f51f02eb172f88636369d59645cb38dee38cc864f59`, 4719 bytes)
    - `materials/deployment/proxy/Dockerfile` ← `work/materials/pwn-v11/gh-bcbf8e4258381230e5ce1de7/build/proxy/Dockerfile` (`bd6cd42300f539302d48d4699ea1090d987303053bce8ecf423c5ab07c9bcdb1`, 331 bytes)
    - `materials/deployment/proxy/team_token_proxy.py` ← `work/materials/pwn-v11/gh-bcbf8e4258381230e5ce1de7/build/proxy/team_token_proxy.py` (`a4cb7d63cf3ed763d3d191a61aebc946efecaa560533958f8a5cad782c416495`, 7675 bytes)
    - `materials/deployment/service/Dockerfile` ← `work/materials/pwn-v11/gh-bcbf8e4258381230e5ce1de7/build/service/Dockerfile` (`f89af63799d68c0048cdf93c380866208d6c66b04f77791e4e0adb5cd8f9c6c9`, 764 bytes)

### 42. `saj-2021-pwn-middleagedheap` — Middleagedheap

- Identity: b01lers / 2021 / Pwn
- Source: `b01lers/b01lers-ctf-2021`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/b01lers/2021/pwn/Middleagedheap`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `bundled_libc_only`; `stack_rop`
- Selection reason: adds event b01lers; adds source b01lers/b01lers-ctf-2021
- Material fingerprint: `14aba19cb56aba43b0906e18bb51fc7a10fc9b2b0f7745e7cee02b4cfcfa2e4a`
- Material paths:
  - A (5):
    - `materials/attachments/description.md` ← `work/materials/pwn-v11/saj-2021-pwn-middleagedheap/public/description.md` (`829de58c6e6462e4ed76f0a6a72a94e8590c2d7974cc4e62d0aebff4f619cbe4`, 165 bytes)
    - `materials/attachments/libc-2.32.so` ← `work/materials/pwn-v11/saj-2021-pwn-middleagedheap/public/libc-2.32.so` (`d48f0edffda549cfb524378027d0b997a77a2dd9ea4f69fe3fd553eb1772050b`, 1995896 bytes)
    - `materials/attachments/middleagedheap` ← `work/materials/pwn-v11/saj-2021-pwn-middleagedheap/public/middleagedheap` (`1c5a2bef9c77296fb4c7f7a19ea0887374bec911c7a9af5f64b3a4fc2f2e4e57`, 19000 bytes)
    - `materials/attachments/middleagedheap.c` ← `work/materials/pwn-v11/saj-2021-pwn-middleagedheap/public/middleagedheap.c` (`af8cc17f8865c183fe98d84ee1d0868b920575ea0db706497632466fb844c489`, 2290 bytes)
    - `materials/attachments/wrapper.sh` ← `work/materials/pwn-v11/saj-2021-pwn-middleagedheap/public/wrapper.sh` (`20ff90ebe29052cf06206c20b8a2d67b099078f424e3f2b4d7cde5a1005decf5`, 57 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solve/solve.py` ← `work/materials/pwn-v11/saj-2021-pwn-middleagedheap/solve/solve/solve.py` (`a70e9827ff666919646c37187a210e147bf64eb1444541975cbfbbc47f528ac9`, 2753 bytes)
  - B (6):
    - `materials/deployment/deploy/Dockerfile` ← `work/materials/pwn-v11/saj-2021-pwn-middleagedheap/build/deploy/Dockerfile` (`3880febe2fffc88403ad305be347ce80e73e00fdda4e18ec739bd93663cb676a`, 698 bytes)
    - `materials/deployment/deploy/Dockerfile-build` ← `work/materials/pwn-v11/saj-2021-pwn-middleagedheap/build/deploy/Dockerfile-build` (`9804c3cc7d6ebf1b6397cf2cffbfd3871a02b7f1b0d9cbe458e03ca05268e1e6`, 639 bytes)
    - `materials/deployment/deploy/docker-compose.yml` ← `work/materials/pwn-v11/saj-2021-pwn-middleagedheap/build/deploy/docker-compose.yml` (`7ce6dfbedca3db1b6b14524ed1b035617c9cd69941d1a2b5775232260377fc0d`, 587 bytes)
    - `materials/deployment/deploy/wrapper.sh` ← `work/materials/pwn-v11/saj-2021-pwn-middleagedheap/build/deploy/wrapper.sh` (`20ff90ebe29052cf06206c20b8a2d67b099078f424e3f2b4d7cde5a1005decf5`, 57 bytes)
    - `materials/deployment/src/Makefile` ← `work/materials/pwn-v11/saj-2021-pwn-middleagedheap/build/src/Makefile` (`9619d6267613678b539a12447c51d20500cacf796bceaaf62e39d0e1636d8f61`, 102 bytes)
    - `materials/deployment/src/middleagedheap.c` ← `work/materials/pwn-v11/saj-2021-pwn-middleagedheap/build/src/middleagedheap.c` (`af8cc17f8865c183fe98d84ee1d0868b920575ea0db706497632466fb844c489`, 2290 bytes)

### 43. `saj-2025-pwn-outdated` — Outdated

- Identity: SekaiCTF / 2025 / Pwn
- Source: `project-sekai-ctf/sekaictf-2025`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/SekaiCTF/2025/pwn/Outdated`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `musl`; `vm_emulator`
- Selection reason: adds event SekaiCTF; adds source project-sekai-ctf/sekaictf-2025
- Material fingerprint: `48ba44e09ff565edb18b6a6d3da1933c934ef681710dc1f398d0709dffba6fbe`
- Material paths:
  - A (4):
    - `materials/attachments/libc.so` ← `work/materials/pwn-v11/saj-2025-pwn-outdated/public/libc.so` (`4548d1f840f42ccfeed05a478a9c57841af30876faf70ce13c5c9480f1cc0207`, 922816 bytes)
    - `materials/attachments/outdated.c` ← `work/materials/pwn-v11/saj-2025-pwn-outdated/public/outdated.c` (`fed073bdcfb9047b3bebff7ae0d707355a83c257d52153d208fb649bdd158aec`, 2349 bytes)
    - `materials/attachments/outdated.py` ← `work/materials/pwn-v11/saj-2025-pwn-outdated/public/outdated.py` (`25cfeb75643c482b413461616651b35e67a78ace9a296f4b81bd09ed3bd6e839`, 4647 bytes)
    - `materials/attachments/pwn_outdated/outdated` ← `work/materials/pwn-v11/saj-2025-pwn-outdated/public/pwn_outdated/outdated` (`08a0aa5801a5ec38bffd818058168ff476cb6490b5ad9d330b1ca62f3e317a75`, 67132 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2025-pwn-outdated/writeups/README.md` (`fda6803702d2a8051b8e6c46aec9995ded7d93eac340263e0408665a266b8855`, 2779 bytes)
  - P (1):
    - `materials/exploit/solution/solve.py` ← `work/materials/pwn-v11/saj-2025-pwn-outdated/solve/solution/solve.py` (`458456533d15e37253265879b3a4ef054375a844ebd70cac572a1c365b0244a1`, 3274 bytes)
  - B (4):
    - `materials/deployment/challenge/Dockerfile` ← `work/materials/pwn-v11/saj-2025-pwn-outdated/build/challenge/Dockerfile` (`d799d81e03642f4135cfeade4525202e3f2318a00cb16e2fc1512b8025761113`, 166 bytes)
    - `materials/deployment/challenge/docker-compose.yml` ← `work/materials/pwn-v11/saj-2025-pwn-outdated/build/challenge/docker-compose.yml` (`b667be29acd980b5df720e130bc1ab6b3de2d6aeeff2ea0e91f6057bb7a8e1f5`, 81 bytes)
    - `materials/deployment/challenge/src/Makefile` ← `work/materials/pwn-v11/saj-2025-pwn-outdated/build/challenge/src/Makefile` (`5e6067ad5f4fc1bffacedf7f79eff1231b4deebc4812d7dada9dc31751f73036`, 175 bytes)
    - `materials/deployment/challenge/src/outdated.c` ← `work/materials/pwn-v11/saj-2025-pwn-outdated/build/challenge/src/outdated.c` (`fed073bdcfb9047b3bebff7ae0d707355a83c257d52153d208fb649bdd158aec`, 2349 bytes)

### 44. `gh-0e6a64119220530e1d497576` — maze-solver

- Identity: CJ CTF / 2020 / Pwn
- Source: `maulvialf/CTF-Challs-Archive`; `https://github.com/maulvialf/CTF-Challs-Archive/tree/5347e5db1a2b2e8381603126a2a236ede111f45d/2020/CJ2020-Final-CTF/pwn/maze-solver`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile_compose`; `nonstandard`; `unknown_or_non_elf`; `other`
- Selection reason: adds event CJ CTF; adds source maulvialf/CTF-Challs-Archive
- Material fingerprint: `d26ee5349107dcae1b03cb8d98f5dd0a938647c88e3e05d38a34a22d9bcdf225`
- Material paths:
  - A (3):
    - `materials/attachments/example1.txt` ← `work/materials/pwn-v11/gh-0e6a64119220530e1d497576/public/example1.txt` (`d49dc56e44bbc6b10190c307a62c2fd29bb10abbf05acfb1069fa63c68d300b6`, 46 bytes)
    - `materials/attachments/example2.txt` ← `work/materials/pwn-v11/gh-0e6a64119220530e1d497576/public/example2.txt` (`998a9ef39ed9c2c07b7d4d51133954e5d3ef44bfd3dfd16918f4cebe3cc8d6f1`, 116 bytes)
    - `materials/attachments/example3.txt` ← `work/materials/pwn-v11/gh-0e6a64119220530e1d497576/public/example3.txt` (`c0fc84c4777381afb045204fea61cfaab6cedd3f97cc57d62b810e6bf08f90b3`, 34 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/service/maze_solver` ← `work/materials/pwn-v11/gh-0e6a64119220530e1d497576/solve/service/maze_solver` (`f1fecdc896eeab5920e61b667a3d052f38013614922dc5efde29a55e5f0f43fd`, 10368 bytes)
  - B (2):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-0e6a64119220530e1d497576/build/Dockerfile` (`d9925dac5d7d27b26d49c1fbd2c54bc29cb64a7b3fe760a66eec0636a389d3eb`, 601 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/gh-0e6a64119220530e1d497576/build/docker-compose.yml` (`166a093e94e980da79772503742c33883779aa228dd391392f56683c3bb37b89`, 121 bytes)

### 45. `saj-2021-pwn-university-pwn` — University_Pwn

- Identity: Tamil / 2021 / Pwn
- Source: `jopraveen/TamilCTF2021`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/Tamil/2021/pwn/University_Pwn`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `bundled_loader_only`; `heap`
- Selection reason: adds event Tamil; adds source jopraveen/TamilCTF2021
- Material fingerprint: `70074574df5b93c3315bb06aaf189a96a5b4e56b3b3ddf7d9ceaa40feb96b9c3`
- Material paths:
  - A (13):
    - `materials/attachments/akka_university` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/public/akka_university` (`8920ac271556405e38185d9b9d93c7cca879c77993fc67aba7b8ff9fb12a5bfe`, 21912 bytes)
    - `materials/attachments/chall4.c` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/public/chall4.c` (`e4760a050dcbfbd95606f28c85acec4be0e2fc89bff044e292d19a6b28ca395b`, 5168 bytes)
    - `materials/attachments/checksec.png` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/public/checksec.png` (`46aac83d07111e231279bb833cd50f15d704ff2159686d6ff1fd9d753f1f2b17`, 6789 bytes)
    - `materials/attachments/gotshell.gif` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/public/gotshell.gif` (`2549026cf3d542e0c5830f8bd85f303a909b1c15e5dcce109d35d504e99ed40e`, 15488 bytes)
    - `materials/attachments/ld-2.31.so` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/public/ld-2.31.so` (`96493303ba8ba364a8da6b77fbb9f04d0f170cbecbc6bbacca616161bd0f0008`, 191472 bytes)
    - `materials/attachments/libc6_2.31-0ubuntu9.2_amd64.so` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/public/libc6_2.31-0ubuntu9.2_amd64.so` (`09d4dc50d7b31bca5fbbd60efebe4ce2ce698c46753a7f643337a303c58db541`, 2029224 bytes)
    - `materials/attachments/menu.png` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/public/menu.png` (`b18ce093e98497905b2e65376b49c7c187747c89506038ce6f9c755355783079`, 8941 bytes)
    - `materials/attachments/note1.png` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/public/note1.png` (`514ca4cb6dd7900611a4e69f6bcf36a2d51579f0188f734b001971f99af49754`, 7235 bytes)
    - `materials/attachments/note2.png` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/public/note2.png` (`eed16b3552d4b30d3fec269dbbab53090a24e0a381e5149bf5f5a7afc49c2cbd`, 25607 bytes)
    - `materials/attachments/phase1.png` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/public/phase1.png` (`b5757692d3fd8de74e09317942a6295456b26b0e9bc8404d9483c7918c678c19`, 16549 bytes)
    - `materials/attachments/sheet.struct.png` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/public/sheet.struct.png` (`0de4728fa3daa2b67bf3218582da73f4a9d0d7d2b5dbb3d2360b5bcdea74a9a9`, 29898 bytes)
    - `materials/attachments/tcache1.png` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/public/tcache1.png` (`3b164e3b94c45e99d2d39570f84002c63778b2709317ba50eefdb45746e34aa1`, 29339 bytes)
    - `materials/attachments/vuln1.png` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/public/vuln1.png` (`95a9f127403b7edc0ad0e1cceb73e11f918597a86ecb664153d610049d78aeaf`, 50163 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/writeups/README.md` (`1ff509897b73232d782eae37cee1496273a4cddeba959d6faf68b5c7f838dba7`, 9017 bytes)
  - P (4):
    - `materials/exploit/Akka_university_exploit.py` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/solve/Akka_university_exploit.py` (`4c3309d09e61b316e89bccf6839d8d1f120631bfaf252f510930ce479fec8876`, 4184 bytes)
    - `materials/exploit/exploit.py` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/solve/exploit.py` (`2577a08fb73e744b1ce8fceb96a74c4c20eebf552f61ef137148a5c400439f44`, 1676 bytes)
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/solve/solve.py` (`33747cf4c8f7ea0570a3c4c3512eb57b98f89385d2628b9d2ea0e9a22e19467e`, 464 bytes)
    - `materials/exploit/working.exploit.py` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/solve/working.exploit.py` (`5d1377ba0c69710345b7cf0ebb252653c0013252a84edf427470fed8bffd99b4`, 3130 bytes)
  - B (2):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/build/Dockerfile` (`e3b2157e30a623165fb1c8d940a17c5f39b095be56369296f27a04dfb472544d`, 444 bytes)
    - `materials/deployment/chall4.c` ← `work/materials/pwn-v11/saj-2021-pwn-university-pwn/build/chall4.c` (`e4760a050dcbfbd95606f28c85acec4be0e2fc89bff044e292d19a6b28ca395b`, 5168 bytes)

### 46. `gh-46a73bbde9c0c5b1eaf50a85` — brainfast

- Identity: hxpctf / 2025 / Pwn
- Source: `hax1ng/hxpctf2025`; `https://github.com/hax1ng/hxpctf2025/tree/61d0406d8d0ea89df7c192731d27a626a5b1beae/pwn/brainfast`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile_compose`; `prebuilt_rehost`; `musl`; `shellcode_seccomp`, `stack_rop`
- Selection reason: adds event hxpctf; adds source hax1ng/hxpctf2025
- Material fingerprint: `10e2ffc4c24f5400e12d13825e942ec4b81c409e30fbb4457537b52f2c5b280f`
- Material paths:
  - A (2):
    - `materials/attachments/vuln` ← `work/materials/pwn-v11/gh-46a73bbde9c0c5b1eaf50a85/public/vuln` (`c74a0488f76226ea718a1bd09ea6c3c7011ce25f176b3912aa0d661d0bdeeb68`, 19744 bytes)
    - `materials/attachments/ynetd` ← `work/materials/pwn-v11/gh-46a73bbde9c0c5b1eaf50a85/public/ynetd` (`c44fadb861e8b6f223da0b4e27e5075c161e797c9a8d72cf8f379fdc7b22dcb4`, 18168 bytes)
  - W: absent
  - P (2):
    - `materials/exploit/exploit.py` ← `work/materials/pwn-v11/gh-46a73bbde9c0c5b1eaf50a85/solve/exploit.py` (`9d5ee418c1fbdce19f985b98fce5be108aa4d1a54527ad64e9f3081c9f67f77c`, 5638 bytes)
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/gh-46a73bbde9c0c5b1eaf50a85/solve/solve.py` (`918335e66799597743611d2105f6d49c9c377e89ec47e9dfa4ccb485110e7b66`, 1700 bytes)
  - B (2):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-46a73bbde9c0c5b1eaf50a85/build/Dockerfile` (`0eb47d2b22def76a7c842bea498050490c6624f0cb23b8386842983a0bac3325`, 450 bytes)
    - `materials/deployment/compose.yml` ← `work/materials/pwn-v11/gh-46a73bbde9c0c5b1eaf50a85/build/compose.yml` (`8668bf272968931f70628a976125371d6f15bea7dfd3562fad4a0d1412d16c85`, 214 bytes)

### 47. `saj-2024-pwn-fl-support-center` — FL_Support_Center

- Identity: TSG / 2024 / Pwn
- Source: `tsg-ut/tsgctf`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/TSG/2024/pwn/FL_Support_Center`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `system_libc`; `heap`
- Selection reason: adds event TSG; adds source tsg-ut/tsgctf
- Material fingerprint: `80d5b4738326ded58ee163de88e06b0198aabd025b380dde581d440bd25881cd`
- Material paths:
  - A (4):
    - `materials/attachments/FL_Support_Center/build/ctf.conf` ← `work/materials/pwn-v11/saj-2024-pwn-fl-support-center/public/FL_Support_Center/build/ctf.conf` (`961c10eb7cf5b7b95fd8ee27c69394decb0293bc2ecd1d7ff9db0e7e488917f4`, 253 bytes)
    - `materials/attachments/FL_Support_Center/build/nginx.conf` ← `work/materials/pwn-v11/saj-2024-pwn-fl-support-center/public/FL_Support_Center/build/nginx.conf` (`192b11875b3ae721f63b8a596014c18d3ca288be50f7610566dd97427700b4bd`, 151 bytes)
    - `materials/attachments/FL_Support_Center/fl_support_center` ← `work/materials/pwn-v11/saj-2024-pwn-fl-support-center/public/FL_Support_Center/fl_support_center` (`3495f61aa1fe15b0521be06f1f976e407c41e4bc9210c054d6d95aa867a2e44b`, 77000 bytes)
    - `materials/attachments/FL_Support_Center/main.cpp` ← `work/materials/pwn-v11/saj-2024-pwn-fl-support-center/public/FL_Support_Center/main.cpp` (`45239396fac6f4d6270ab779eb779325ff2d04440675e48b499dc13a63d8f5fb`, 4857 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2024-pwn-fl-support-center/writeups/README.md` (`fda926b352ac3f7d1e64710a33342d41f1633629414c544473bb6575b05220fe`, 157 bytes)
  - P (1):
    - `materials/exploit/exp.py` ← `work/materials/pwn-v11/saj-2024-pwn-fl-support-center/solve/exp.py` (`b62d59ca4be495c96dabcd11b9bcea924086ffbb4b019b401b0fb88a92ac6a9c`, 3247 bytes)
  - B (4):
    - `materials/deployment/FL_Support_Center/Dockerfile` ← `work/materials/pwn-v11/saj-2024-pwn-fl-support-center/build/FL_Support_Center/Dockerfile` (`9b8a0dc640541472489403b0de3592639896515693b03f7a44785ad746132d6c`, 737 bytes)
    - `materials/deployment/FL_Support_Center/build/start.sh` ← `work/materials/pwn-v11/saj-2024-pwn-fl-support-center/build/FL_Support_Center/build/start.sh` (`47481d3bbc3642d9bf29601620e3ba6d2e2e836b660b7a18140927333b67b749`, 94 bytes)
    - `materials/deployment/FL_Support_Center/docker-compose.yml` ← `work/materials/pwn-v11/saj-2024-pwn-fl-support-center/build/FL_Support_Center/docker-compose.yml` (`4203b319ac00a296a0192cdd8865ab9b1bff8fffb30b44545d6478f69eee1de8`, 638 bytes)
    - `materials/deployment/FL_Support_Center/main.cpp` ← `work/materials/pwn-v11/saj-2024-pwn-fl-support-center/build/FL_Support_Center/main.cpp` (`45239396fac6f4d6270ab779eb779325ff2d04440675e48b499dc13a63d8f5fb`, 4857 bytes)

### 48. `saj-2026-pwn-goodbye-libc` — Goodbye_libc

- Identity: TAMUctf / 2026 / Pwn
- Source: `tamuctf/tamuctf-2024`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/TAMUctf/2026/pwn/Goodbye_libc`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `build_metadata`; `hybrid`; `bundled_loader_only`; `other`
- Selection reason: adds event TAMUctf; adds source tamuctf/tamuctf-2024
- Material fingerprint: `53d186d86276545b5437b482d25695049cf0d04d3448d5d2a8c38c6fd405fbbf`
- Material paths:
  - A (6):
    - `materials/attachments/goodbye-libc/bye-libc.c` ← `work/materials/pwn-v11/saj-2026-pwn-goodbye-libc/public/goodbye-libc/bye-libc.c` (`a42f20cbb697a74e84797bbe5ff338de180fe23170a0b901fc78f6f870ab1948`, 812 bytes)
    - `materials/attachments/goodbye-libc/bye-libc.h` ← `work/materials/pwn-v11/saj-2026-pwn-goodbye-libc/public/goodbye-libc/bye-libc.h` (`d507615476a842a182d963feee6c5000a6fac7f6c1dbdcc3294e8e2e4893a75c`, 137 bytes)
    - `materials/attachments/goodbye-libc/goodbye-libc` ← `work/materials/pwn-v11/saj-2026-pwn-goodbye-libc/public/goodbye-libc/goodbye-libc` (`259fc0b49e3b97f9a495332fbf3525d5dbecb3fbd68a3f29643d7ea849dbc8a2`, 14432 bytes)
    - `materials/attachments/goodbye-libc/goodbye-libc.c` ← `work/materials/pwn-v11/saj-2026-pwn-goodbye-libc/public/goodbye-libc/goodbye-libc.c` (`d35b89e7c12ac9702f81e3aaaadd96a9ff44fc513183353fb4eff12c7db87517`, 5410 bytes)
    - `materials/attachments/goodbye-libc/ld-linux-x86-64.so.2` ← `work/materials/pwn-v11/saj-2026-pwn-goodbye-libc/public/goodbye-libc/ld-linux-x86-64.so.2` (`593bb1d5355658e645f36e6b1f49832691b24e177209765914e4cce51499dbb4`, 215000 bytes)
    - `materials/attachments/goodbye-libc/libbye-libc.so` ← `work/materials/pwn-v11/saj-2026-pwn-goodbye-libc/public/goodbye-libc/libbye-libc.so` (`4aabcb884d9a811ea1bbbbb625bad3d52f597a8437bf66463abcb613651d5e9d`, 13560 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/goodbye-libc/solver-template.py` ← `work/materials/pwn-v11/saj-2026-pwn-goodbye-libc/solve/goodbye-libc/solver-template.py` (`2a5c5c4c0755f890f7d01787098cd8e48a0199f6077f08dfd8321541d54010f5`, 143 bytes)
  - B (3):
    - `materials/deployment/goodbye-libc/bye-libc.c` ← `work/materials/pwn-v11/saj-2026-pwn-goodbye-libc/build/goodbye-libc/bye-libc.c` (`a42f20cbb697a74e84797bbe5ff338de180fe23170a0b901fc78f6f870ab1948`, 812 bytes)
    - `materials/deployment/goodbye-libc/bye-libc.h` ← `work/materials/pwn-v11/saj-2026-pwn-goodbye-libc/build/goodbye-libc/bye-libc.h` (`d507615476a842a182d963feee6c5000a6fac7f6c1dbdcc3294e8e2e4893a75c`, 137 bytes)
    - `materials/deployment/goodbye-libc/goodbye-libc.c` ← `work/materials/pwn-v11/saj-2026-pwn-goodbye-libc/build/goodbye-libc/goodbye-libc.c` (`d35b89e7c12ac9702f81e3aaaadd96a9ff44fc513183353fb4eff12c7db87517`, 5410 bytes)

### 49. `saj-2023-pwn-n0tes-revenge` — n0tes-revenge

- Identity: BSidesTLV / 2023 / Pwn
- Source: `bsidestlv/ctf20-public`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/BSidesTLV/2023/pwn/n0tes-revenge`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile`; `prebuilt_rehost`; `bundled_libc_only`; `stack_rop`
- Selection reason: adds event BSidesTLV; adds source bsidestlv/ctf20-public
- Material fingerprint: `7d630b15bb6f5943b7d0332e6f382595765ed8f3c81d05a8bdb40eaa344bd7bf`
- Material paths:
  - A (6):
    - `materials/attachments/README.md` ← `work/materials/pwn-v11/saj-2023-pwn-n0tes-revenge/public/README.md` (`a5e5dcd919c09960186dde081879d6be5021a5b247e1da863a0eb516801f5a42`, 127 bytes)
    - `materials/attachments/banner.txt` ← `work/materials/pwn-v11/saj-2023-pwn-n0tes-revenge/public/banner.txt` (`081658c904d7500fdf8a051f67968c1ebfd4b88b5524bfbbb6c76f5a85ae81d0`, 153 bytes)
    - `materials/attachments/chall_image.jpg` ← `work/materials/pwn-v11/saj-2023-pwn-n0tes-revenge/public/chall_image.jpg` (`099abda91d5154e9abd8bb5aaea7675a3ad318123152ba047b37f09563c5e8d6`, 88252 bytes)
    - `materials/attachments/libc.so.6` ← `work/materials/pwn-v11/saj-2023-pwn-n0tes-revenge/public/libc.so.6` (`436bf9e45334ab7e44fa78ab06d2578af34eac8dece2b4cb373ba4be73dac86c`, 1922136 bytes)
    - `materials/attachments/n0tes-revenge` ← `work/materials/pwn-v11/saj-2023-pwn-n0tes-revenge/public/n0tes-revenge` (`714cb63e848254596c29e11ff4da3648458a49c4572db9fc80fd5f85a33103c2`, 12056 bytes)
    - `materials/attachments/solved_image.jpg` ← `work/materials/pwn-v11/saj-2023-pwn-n0tes-revenge/public/solved_image.jpg` (`45c5770bbdafe1d08334cc8a48b56055ab7acc8ce4bd36aa4a85404aca93b6ac`, 55435 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2023-pwn-n0tes-revenge/writeups/README.md` (`9ae33f9218e513a5d2619b4e06b7eaf45e3c69d6aec34e4d339b8009dc7062eb`, 22942 bytes)
  - P (1):
    - `materials/exploit/working.exploit.py` ← `work/materials/pwn-v11/saj-2023-pwn-n0tes-revenge/solve/working.exploit.py` (`dcee32627d88f270c4866811c4ef8c95f80a15a03fdd086e134c35a26bc0f139`, 1837 bytes)
  - B (1):
    - `materials/deployment/extraced/Dockerfile` ← `work/materials/pwn-v11/saj-2023-pwn-n0tes-revenge/build/extraced/Dockerfile` (`833faac9ca7fc81202d0de6f5f941677a57e9f0efc63233fd79157a5d7153a0e`, 689 bytes)

### 50. `gh-c8994bfe8e2d35da8fa6611b` — 38 baby-aarch64

- Identity: cuhk ctf / 2024 / Pwn
- Source: `CUHK0x/cuhk-ctf-2024-challenges`; `https://github.com/CUHK0x/cuhk-ctf-2024-challenges/tree/ce031c9277611848f7784e1b5797c84b05b4faba/pwn/38_baby-aarch64`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `static`; `format_string`, `shellcode_seccomp`, `vm_emulator`
- Selection reason: adds event cuhk ctf; adds source CUHK0x/cuhk-ctf-2024-challenges
- Material fingerprint: `d4d84420bc6fbd2cf6fc1abb63cd61a0022ae16d91b729b0d6fd6e75c6552e1d`
- Material paths:
  - A (3):
    - `materials/attachments/chall` ← `work/materials/pwn-v11/gh-c8994bfe8e2d35da8fa6611b/public/chall` (`d337c5d8c898ac63322976e0560bbd7d1fbbb2303410807847c68d4f527b4e81`, 649880 bytes)
    - `materials/attachments/ctf.xinetd` ← `work/materials/pwn-v11/gh-c8994bfe8e2d35da8fa6611b/public/ctf.xinetd` (`1c7cff4d64324e62ea00193f9bbea71706a4403690c5c03bec8df1d0b23c5778`, 572 bytes)
    - `materials/attachments/logo` ← `work/materials/pwn-v11/gh-c8994bfe8e2d35da8fa6611b/public/logo` (`fd259644e612baa102e3bf970939ace07b28c801f92f6accc9cf26af765d5773`, 270 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/writeup/solve.py` ← `work/materials/pwn-v11/gh-c8994bfe8e2d35da8fa6611b/solve/writeup/solve.py` (`0b9cff486d3ac249b418c35aa54f1f42ae7183c566e2528ceb871de04d995c69`, 1305 bytes)
  - B (7):
    - `materials/deployment/deploy/Dockerfile` ← `work/materials/pwn-v11/gh-c8994bfe8e2d35da8fa6611b/build/deploy/Dockerfile` (`3a825808a2bafce6da4622a4a45bd2d4b4f484582772f59ed03251e26f584a01`, 553 bytes)
    - `materials/deployment/deploy/bin/start.sh` ← `work/materials/pwn-v11/gh-c8994bfe8e2d35da8fa6611b/build/deploy/bin/start.sh` (`c1251eb525ba9f56a2481b883eea63079bcc184ab5755c340bd68eb281aafafc`, 78 bytes)
    - `materials/deployment/deploy/docker-compose.yaml` ← `work/materials/pwn-v11/gh-c8994bfe8e2d35da8fa6611b/build/deploy/docker-compose.yaml` (`dd27e3245e647d0b6a02fc37a1252d4592f44354273c7c976fc1c8880fc615b4`, 121 bytes)
    - `materials/deployment/deploy/start.sh` ← `work/materials/pwn-v11/gh-c8994bfe8e2d35da8fa6611b/build/deploy/start.sh` (`b8ba4450e654f46e81fdd8b1db93ccc7a212165f7914469e667edfddd6cc44a7`, 52 bytes)
    - `materials/deployment/public/Dockerfile` ← `work/materials/pwn-v11/gh-c8994bfe8e2d35da8fa6611b/build/public/Dockerfile` (`cf23261635f9c3419cbc20ad2763a4a657f02c9e46b7723785f0afac4a61c5c8`, 528 bytes)
    - `materials/deployment/writeup/src/Makefile` ← `work/materials/pwn-v11/gh-c8994bfe8e2d35da8fa6611b/build/writeup/src/Makefile` (`6a5410ab1c9030cc4dc33e8b5601b3e44952bd4855db2ff585ef47a771147e26`, 53 bytes)
    - `materials/deployment/writeup/src/chall.c` ← `work/materials/pwn-v11/gh-c8994bfe8e2d35da8fa6611b/build/writeup/src/chall.c` (`6353e49bc1c5655d5aeec13ec2bf242217f813fc8a0f3b765a15368bc666eae3`, 1885 bytes)

### 51. `saj-2024-pwn-adventure` — Adventure

- Identity: Pearl / 2024 / Pwn
- Source: `CyberLabs-Infosec/PearlCTF_Challenges_Public_2024`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/Pearl/2024/pwn/Adventure`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `bundled_loader_only`; `stack_rop`
- Selection reason: adds event Pearl; adds source CyberLabs-Infosec/PearlCTF_Challenges_Public_2024
- Material fingerprint: `6fe78656e1e5b7f673e15e4d81c643955ab9e492b20dcdff0c58c0c078df65a3`
- Material paths:
  - A (6):
    - `materials/attachments/adventure` ← `work/materials/pwn-v11/saj-2024-pwn-adventure/public/adventure` (`49b4944bfe20b10e2b49725d9c12eb35a803fdb6a9bbbfed17e020be73c9f337`, 20688 bytes)
    - `materials/attachments/adventure.c` ← `work/materials/pwn-v11/saj-2024-pwn-adventure/public/adventure.c` (`82e1e713ece2d433645d4b07da8de3143fa9a147f13b9514ceed738b802fab38`, 5426 bytes)
    - `materials/attachments/adventure_patched` ← `work/materials/pwn-v11/saj-2024-pwn-adventure/public/adventure_patched` (`1f99f454ddfed588fa14971c4bbf371c06aafeb0d05c63ce8cdfc0f47a960725`, 28880 bytes)
    - `materials/attachments/ld-2.35.so` ← `work/materials/pwn-v11/saj-2024-pwn-adventure/public/ld-2.35.so` (`fb1e752417ac218ffb12ea0fedb32b8e82c0f753f933d36e3f90a7679dafc22d`, 240936 bytes)
    - `materials/attachments/libc6_2.35-0ubuntu1_amd64.so` ← `work/materials/pwn-v11/saj-2024-pwn-adventure/public/libc6_2.35-0ubuntu1_amd64.so` (`3971d705b8ef0d2e0a1343df0c3dc91722547da834cd06274a716da05aaca7c0`, 2220064 bytes)
    - `materials/attachments/specify_libc_version.py` ← `work/materials/pwn-v11/saj-2024-pwn-adventure/public/specify_libc_version.py` (`0138b7c581df9758c81ef97f1cc14df381cd0ddf2f1f53f16cb0f525e5856fb0`, 945 bytes)
  - W (1):
    - `materials/writeups/writeup.md` ← `work/materials/pwn-v11/saj-2024-pwn-adventure/writeups/writeup.md` (`67900a296451801f24672c4e9bb762af9e78488aa2a70bbdc00bcde63c391c82`, 444 bytes)
  - P (1):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2024-pwn-adventure/solve/solve.py` (`58060a7c354f045d5dd79adb751c29389ecc0a202867d02c5abe5ec006427863`, 1284 bytes)
  - B (2):
    - `materials/deployment/src/Dockerfile` ← `work/materials/pwn-v11/saj-2024-pwn-adventure/build/src/Dockerfile` (`a59eb31442bc96a4949b53790d2c2d263b0641c152404eb1e70d6a38f8261a87`, 156 bytes)
    - `materials/deployment/src/adventure.c` ← `work/materials/pwn-v11/saj-2024-pwn-adventure/build/src/adventure.c` (`82e1e713ece2d433645d4b07da8de3143fa9a147f13b9514ceed738b802fab38`, 5426 bytes)

### 52. `saj-2022-pwn-ringsofsaturn` — RingsOfSaturn

- Identity: SpaceHeroes / 2022 / Pwn
- Source: `tj-oconnor/spaceheroes_ctf`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/SpaceHeroes/2022/pwn/RingsOfSaturn`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `bundled_libc_loader`; `heap`
- Selection reason: adds event SpaceHeroes; adds source tj-oconnor/spaceheroes_ctf
- Material fingerprint: `d18315aff2d740a8f44e26ff033fa588a97225814d0562b2cbcfbb3a73d0d2ed`
- Material paths:
  - A (11):
    - `materials/attachments/build_local.sh` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/public/build_local.sh` (`e9c9a3b18680db2fe7454bdacc688521a8563330db4602bd7b5706ec116b6de4`, 188 bytes)
    - `materials/attachments/chal.json` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/public/chal.json` (`baa5413e0c92a02ee9fe77f1b396ce6eb4683cef60f08c2536337d677fad2006`, 392 bytes)
    - `materials/attachments/deploy.sh` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/public/deploy.sh` (`4c552d3460561cd4d190ed2244e033ccd0d60ac1ada4f1330fef2465c75940a2`, 68 bytes)
    - `materials/attachments/hexdump.c` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/public/hexdump.c` (`41dea633eeca00a2add364ac56b246edbaff7888330ba0f2621d83a819677d16`, 1169 bytes)
    - `materials/attachments/hexdump.h` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/public/hexdump.h` (`8303b303b4ac5dcd869ef73e392b1ce92c3b48c98e402c57cdc71696435f3940`, 514 bytes)
    - `materials/attachments/ld-2.27.so` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/public/ld-2.27.so` (`39d477bff8ffc9a043fddb90ab256a209c9e2e5bdd5e5b8d542982cebb3df7a0`, 170960 bytes)
    - `materials/attachments/libc.so.6` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/public/libc.so.6` (`f0ad9639b2530741046e06c96270b25da2339b6c15a7ae46de8fb021b3c4f529`, 2030544 bytes)
    - `materials/attachments/rings_of_saturn` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/public/rings_of_saturn` (`6c4e2bfbdc807453f97712ad039b6899a688df9de6bc058ad13df63c9f85c12e`, 13560 bytes)
    - `materials/attachments/rings_of_saturn.c` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/public/rings_of_saturn.c` (`01515445fcfdd028d7c6663c5f4c93b48495e75e1ed7f8aeb818a2a2f061c7fa`, 10431 bytes)
    - `materials/attachments/rings_of_saturn_dbg` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/public/rings_of_saturn_dbg` (`3714d68817b1bc7c428aa56585a697171e2f3a80ce1c7dace76f29d03f7de934`, 17896 bytes)
    - `materials/attachments/wrapper.sh` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/public/wrapper.sh` (`00fdac09c937408793e4fb0596ed27c2ad9f1882240f0015dfd8c046defb6614`, 59 bytes)
  - W: absent
  - P (4):
    - `materials/exploit/deploy/solve.py` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/solve/deploy/solve.py` (`511e2eb046eee834790c445da9f104d9be055b09bb4adfec36800ec7767355d6`, 461 bytes)
    - `materials/exploit/exp.py` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/solve/exp.py` (`30955782d38346fd5e18af863c7b7c30a6a7434594b940427f60298aca13575a`, 2298 bytes)
    - `materials/exploit/solve/solve.py` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/solve/solve/solve.py` (`cce62ad2e813265df77d59d82273b405a94e4e7dd44fee0a92b476481d5578d6`, 5870 bytes)
    - `materials/exploit/solve/solve.py.old` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/solve/solve/solve.py.old` (`82498abb25865afdfa26df2c9e9631e52ed4bffeadafa817ffb93650488de9d1`, 5590 bytes)
  - B (12):
    - `materials/deployment/deploy.sh` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/build/deploy.sh` (`4c552d3460561cd4d190ed2244e033ccd0d60ac1ada4f1330fef2465c75940a2`, 68 bytes)
    - `materials/deployment/deploy/Dockerfile` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/build/deploy/Dockerfile` (`d590743eb2e8306d4608cad160ce90cf1adec2553df4f42ca8108e749022e792`, 1694 bytes)
    - `materials/deployment/deploy/Dockerfile-build` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/build/deploy/Dockerfile-build` (`5111c34a57d643daeefa8e1f3c4460d99fd58287cda6c3dabcc494952d4ca4a4`, 1055 bytes)
    - `materials/deployment/deploy/build_local.sh` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/build/deploy/build_local.sh` (`e9c9a3b18680db2fe7454bdacc688521a8563330db4602bd7b5706ec116b6de4`, 188 bytes)
    - `materials/deployment/solve/Dockerfile` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/build/solve/Dockerfile` (`7bff84d637066fc6b08a6e0949e455cc920281442a936f1a18748953cf9ddf41`, 1644 bytes)
    - `materials/deployment/solve/Dockerfile-build` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/build/solve/Dockerfile-build` (`d20c7fb7c14810e0b7dd330c340b2ef89e04427e29c79c2c1e74906c1693c59b`, 1046 bytes)
    - `materials/deployment/solve/docker-compose.yml` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/build/solve/docker-compose.yml` (`e689e8201a0c94b6b81f2c0e8ac8e23a3477a85140e537329a350bcf4d548bc7`, 587 bytes)
    - `materials/deployment/solve/wrapper.sh` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/build/solve/wrapper.sh` (`00fdac09c937408793e4fb0596ed27c2ad9f1882240f0015dfd8c046defb6614`, 59 bytes)
    - `materials/deployment/src/Makefile` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/build/src/Makefile` (`293f5ccdb7c2b9067fb81a20304db12b04afdf4f0c68733f82c0dda6644fa26e`, 354 bytes)
    - `materials/deployment/src/hexdump.c` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/build/src/hexdump.c` (`41dea633eeca00a2add364ac56b246edbaff7888330ba0f2621d83a819677d16`, 1169 bytes)
    - `materials/deployment/src/hexdump.h` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/build/src/hexdump.h` (`8303b303b4ac5dcd869ef73e392b1ce92c3b48c98e402c57cdc71696435f3940`, 514 bytes)
    - `materials/deployment/src/rings_of_saturn.c` ← `work/materials/pwn-v11/saj-2022-pwn-ringsofsaturn/build/src/rings_of_saturn.c` (`01515445fcfdd028d7c6663c5f4c93b48495e75e1ed7f8aeb818a2a2f061c7fa`, 10431 bytes)

### 53. `gh-6ad778ed7e813f9851364036` — window

- Identity: imaginaryctf / 2023 / Pwn
- Source: `ret2school/ctf`; `https://github.com/ret2school/ctf/tree/c1566b5a1d24f11772e2e1c2edb286b24469f1bb/2023/imaginaryctf/pwn/window`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `build_metadata`; `hybrid`; `static`; `kernel`
- Selection reason: adds event imaginaryctf; adds source ret2school/ctf
- Material fingerprint: `ccfc0a026c72f50c84ea3cbe6c4ed1dc98e9d365575821e2a74ba5ecf7334729`
- Material paths:
  - A (17):
    - `materials/attachments/bin/busybox` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/public/bin/busybox` (`5f0fc139aaa912a5e73166b67c4dc817cdc859d80f15f82fd7150193fbc9d688`, 2701792 bytes)
    - `materials/attachments/bzImage` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/public/bzImage` (`f725b7781135a136742ebc9cbc20f699f6494c909310db585c163cf6a8658fdb`, 12200840 bytes)
    - `materials/attachments/chall.ko` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/public/chall.ko` (`3a514f5b21de8d438e13548e40c771fa56244c83f6840ff715e4b4eae6471aec`, 200464 bytes)
    - `materials/attachments/chall.ko.i64` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/public/chall.ko.i64` (`acfd757de69a5de214b57a61d5fc521c87a960cd19751ae8e205741e95dae393`, 251084 bytes)
    - `materials/attachments/chall.ko.id0` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/public/chall.ko.id0` (`6ab10731df072ef556b27db31c83a3c7307510e08f001405abcdde2375979171`, 147456 bytes)
    - `materials/attachments/chall.ko.id1` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/public/chall.ko.id1` (`513b482d624f470bce093b5fdaed8a00c684802da3c11036bc6c10e0f478d9ea`, 24576 bytes)
    - `materials/attachments/chall.ko.id2` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/public/chall.ko.id2` (`865959b84ddcf0eceff5e91483ca157138a35f70885de2c606a5b62da4ceaf1e`, 440 bytes)
    - `materials/attachments/chall.ko.nam` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/public/chall.ko.nam` (`1e6dbc04e25cf7bf7b45005106955235b8de037b3f4bd27f40f469a6abb45ee3`, 16384 bytes)
    - `materials/attachments/chall.ko.til` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/public/chall.ko.til` (`f95cde3ca6dfacd9d7f707eab0b4449fb57e85541abe6686e2d77774d45b39ba`, 61931 bytes)
    - `materials/attachments/decompress.sh` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/public/decompress.sh` (`e27bbb34543b0cbb1718196b93ec36ceec6ebbb76205ba8b3fa41ece498d0add`, 78 bytes)
    - `materials/attachments/etc/init.d/rcS` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/public/etc/init.d/rcS` (`852c1cab3148074cfe0a808cf84bf9d4adab85ddc0483d762fae072b89b26cc2`, 1539 bytes)
    - `materials/attachments/etc/motd` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/public/etc/motd` (`e40382b290e0a543d012717ddf5f14192041a3059cded69f0612fcd5637af7bf`, 542 bytes)
    - `materials/attachments/etc/profile` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/public/etc/profile` (`ae4e49a01b4e742852c3cf8cc986b961cfb3ee1d6b43985398a3104d9d9ec055`, 14 bytes)
    - `materials/attachments/extract-vmlinux` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/public/extract-vmlinux` (`97cfeeeb51de17f4b5928c5442b56e5581314ddef3cedf2523be2049d79394af`, 1695 bytes)
    - `materials/attachments/gdb.sh` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/public/gdb.sh` (`94a01120ef5b1d016edd76a4b72c78ed6ad7b61aaaa145722afe3347972da752`, 29 bytes)
    - `materials/attachments/initramfs.cpio` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/public/initramfs.cpio` (`33db644098aad699c69787b8a6d6e7671a44b6bcc457533b74c24675c45cab0e`, 3500032 bytes)
    - `materials/attachments/vmlinux` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/public/vmlinux` (`82339a964577a935f4893f0456fc6b75d2c07009c3f10476bf35f87559803dfe`, 58098148 bytes)
  - W (1):
    - `materials/writeups/iwindow.md` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/writeups/iwindow.md` (`1846136959838c3354b7e938814d6f13aa92b6a1abbb73db1f797ee96f9f8262`, 10722 bytes)
  - P (3):
    - `materials/exploit/opportunity/initramfs/exploit` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/solve/opportunity/initramfs/exploit` (`669e36d09c5880ceafa08d7354caec3ca6384b72aa4b904d8efd362bae8a656a`, 34040 bytes)
    - `materials/exploit/opportunity/src/exploit` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/solve/opportunity/src/exploit` (`0f0a4ab700c1b5f4f590824dad9977712458633942d3e46fe8654262ec3451fe`, 1034944 bytes)
    - `materials/exploit/opportunity/src/exploit.c` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/solve/opportunity/src/exploit.c` (`b92f9199b7e10df7a53184aa4d0db1735ee6f4cca7d870f62ce01e2106b78c19`, 2063 bytes)
  - B (2):
    - `materials/deployment/opportunity/run.sh` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/build/opportunity/run.sh` (`7b92ebb30e98a6f2d7938d6aec71c14d1d1358ddec39d75fe4468fb8363bd585`, 1030 bytes)
    - `materials/deployment/opportunity/src/Makefile` ← `work/materials/pwn-v11/gh-6ad778ed7e813f9851364036/build/opportunity/src/Makefile` (`60677bb4e7ed586d9c75dfe7e86e8374b4992a95930044f5ff1f121ea1ff72d9`, 120 bytes)

### 54. `saj-2024-pwn-format-muscle` — Format_muscle

- Identity: CrewCTF / 2024 / Pwn
- Source: `Thehackerscrew/CrewCTF-2024-Public`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/CrewCTF/2024/pwn/Format_muscle`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `musl`; `other`
- Selection reason: adds event CrewCTF; adds source Thehackerscrew/CrewCTF-2024-Public
- Material fingerprint: `ba45a40552d0c80e0d030dc6cec882578cfa7246b5077e0ec5e9c7667d7ecbb4`
- Material paths:
  - A (2):
    - `materials/attachments/dist/format-muscle` ← `work/materials/pwn-v11/saj-2024-pwn-format-muscle/public/dist/format-muscle` (`5beaff48cc55177b092048409a8e7e4f7403272b9d87fa4ad24dcfac89b890ed`, 24656 bytes)
    - `materials/attachments/dist/libc.so.6` ← `work/materials/pwn-v11/saj-2024-pwn-format-muscle/public/dist/libc.so.6` (`5a19dbe8df0f76fe6a141f54df456d205a89c5e96d73137cd286276af58c9fdf`, 707056 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solve/solve.py` ← `work/materials/pwn-v11/saj-2024-pwn-format-muscle/solve/solve/solve.py` (`2b088aeab57368fd4bdecdcb03bdec6a67acbc99d80a0bd48cd0aff6202cf653`, 1607 bytes)
  - B (3):
    - `materials/deployment/challenge/Dockerfile` ← `work/materials/pwn-v11/saj-2024-pwn-format-muscle/build/challenge/Dockerfile` (`8f0bfdccccb4e4ae840464cb4017643d60d91c0c07524798e09fafaceafb605a`, 263 bytes)
    - `materials/deployment/challenge/run.sh` ← `work/materials/pwn-v11/saj-2024-pwn-format-muscle/build/challenge/run.sh` (`dbb39a7b650b794aa1b1539904ad399bc87a86331557dd8a7f75cc641eff2265`, 85 bytes)
    - `materials/deployment/solve/format-muscle.c` ← `work/materials/pwn-v11/saj-2024-pwn-format-muscle/build/solve/format-muscle.c` (`cf3038f458ba7622e65c889d4da83ad56ab9de46b645a6c01d4d0ec61824c341`, 223 bytes)

### 55. `saj-2022-pwn-asianparents` — AsianParents

- Identity: Balsn / 2022 / Pwn
- Source: `balsn/balsn-ctf-2022`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/Balsn/2022/pwn/AsianParents`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `bundled_libc_only`; `stack_rop`
- Selection reason: adds event Balsn; adds source balsn/balsn-ctf-2022
- Material fingerprint: `1f7dac79fe35b6bad146642cfe07a8838895a136a3fb816bb6ea7207690c9561`
- Material paths:
  - A (9):
    - `materials/attachments/deploy/asianparent/share/chall` ← `work/materials/pwn-v11/saj-2022-pwn-asianparents/public/deploy/asianparent/share/chall` (`d55cd7889f61eceabd8f7d2442404cc69709845c15989ad7d81fdf58e830aea2`, 17104 bytes)
    - `materials/attachments/gotshell.gif` ← `work/materials/pwn-v11/saj-2022-pwn-asianparents/public/gotshell.gif` (`eb64378acdf183e61116dfba53af9a6cc6de4aba99d2fadf41523d1b229de9b8`, 23599 bytes)
    - `materials/attachments/libc.so.6` ← `work/materials/pwn-v11/saj-2022-pwn-asianparents/public/libc.so.6` (`568740b06a8afa26db4874f8cf61985ecbc6dd127f4229416fe95da8f9ec13fb`, 2216304 bytes)
    - `materials/attachments/menu.png` ← `work/materials/pwn-v11/saj-2022-pwn-asianparents/public/menu.png` (`bf3830862e2e88821cb57d59a81a58ec26b6464e0224f320359b95aa0dfc7fe0`, 20635 bytes)
    - `materials/attachments/pwnit.py` ← `work/materials/pwn-v11/saj-2022-pwn-asianparents/public/pwnit.py` (`597e6c4c2793fcf2839f36f9c80401f6d1ac9a86f6210d16fb364d3bd13c935a`, 6027 bytes)
    - `materials/attachments/seccomp_child.png` ← `work/materials/pwn-v11/saj-2022-pwn-asianparents/public/seccomp_child.png` (`160fef12bd9ff441b4dcd2aec84835e1eb296e878b7eafa31d99d18454c97e27`, 46991 bytes)
    - `materials/attachments/seccomp_doc.png` ← `work/materials/pwn-v11/saj-2022-pwn-asianparents/public/seccomp_doc.png` (`51f7cdc7d7ece2d863ac5359f65cb0703a0a934b8b9adc51c7c69a98488aea28`, 153421 bytes)
    - `materials/attachments/seccomp_parent.png` ← `work/materials/pwn-v11/saj-2022-pwn-asianparents/public/seccomp_parent.png` (`72fb3f8a0ce637d7cb3baaea64065558f5256ce00d7aac3124ac50f6ca407e67`, 53308 bytes)
    - `materials/attachments/title.png` ← `work/materials/pwn-v11/saj-2022-pwn-asianparents/public/title.png` (`0815c09b9abf5f4c9681e92ce5bfbd1a96a0da2b4f1b5a40f0380c908e581c33`, 25557 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2022-pwn-asianparents/writeups/README.md` (`82370aeff302ce80ac5a95c4b0c939a5f96fb8996b6b0497ec85ed58f66068e9`, 9614 bytes)
  - P (1):
    - `materials/exploit/working.exploit.py` ← `work/materials/pwn-v11/saj-2022-pwn-asianparents/solve/working.exploit.py` (`0a473a202d4f9b89ab0bd7766cd2ece95a9e9ceadbb8d5ffd3bc7fadbf85e5d3`, 3933 bytes)
  - B (4):
    - `materials/deployment/asianparent/Dockerfile` ← `work/materials/pwn-v11/saj-2022-pwn-asianparents/build/asianparent/Dockerfile` (`a276e4e18726cb119b78fba8bbfe122d60e9b36082086a160b86b7ea4c290b7b`, 314 bytes)
    - `materials/deployment/asianparent/share/run.sh` ← `work/materials/pwn-v11/saj-2022-pwn-asianparents/build/asianparent/share/run.sh` (`2f5263b0b3a8b3170f9ca014689a9a0a06fa6b0e52b7ebc5abf6f6100409b9e2`, 64 bytes)
    - `materials/deployment/asianparent/xinetd` ← `work/materials/pwn-v11/saj-2022-pwn-asianparents/build/asianparent/xinetd` (`74215079789a98283459517f1fb412456ea397aa27fa93404b4767923c4fc844`, 314 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/saj-2022-pwn-asianparents/build/docker-compose.yml` (`685513dc4e413714fadcd250a64c57a9c1fee7f155833962d1f84b9dd061ed13`, 237 bytes)

### 56. `saj-2025-pwn-prospector` — prospector

- Identity: justCTF / 2025 / Pwn
- Source: `justcatthefish/justctf-2025`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/justCTF/2025/pwn/prospector`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `bundled_loader_only`; `stack_rop`
- Selection reason: adds event justCTF; adds source justcatthefish/justctf-2025
- Material fingerprint: `081ad375ca74c1c26945a4516b0f9b405a7fbeb37062b3864102eed579d3371b`
- Material paths:
  - A (6):
    - `materials/attachments/ld-linux-x86-64.so.2` ← `work/materials/pwn-v11/saj-2025-pwn-prospector/public/ld-linux-x86-64.so.2` (`c0b8f7dd05a4975c84b784041a001a4cfa0f4fd4292925687b686551a91e35cc`, 251544 bytes)
    - `materials/attachments/prospector` ← `work/materials/pwn-v11/saj-2025-pwn-prospector/public/prospector` (`c5e0c814d7cdf1d5bea1285f6f2039db6cf8b3018bb351e93ce8e7952aa117d2`, 13368 bytes)
    - `materials/attachments/prospector.py` ← `work/materials/pwn-v11/saj-2025-pwn-prospector/public/prospector.py` (`d029ad9ed6d0ba5ed4cdfe3c1e369346fda52e2ed4ee5c4336ba89c74e8ae9e9`, 9691 bytes)
    - `materials/attachments/prospector_patched` ← `work/materials/pwn-v11/saj-2025-pwn-prospector/public/prospector_patched` (`357bdf910bb19db166168881811f3c60ba8525682a18dfeb28cde15ff5f3a07e`, 16545 bytes)
    - `materials/attachments/test` ← `work/materials/pwn-v11/saj-2025-pwn-prospector/public/test` (`8ed073ce49b8230483976bc30eceae90e956ffdf8cc1a80c7e151302975d2d55`, 16088 bytes)
    - `materials/attachments/test.c` ← `work/materials/pwn-v11/saj-2025-pwn-prospector/public/test.c` (`928b1bed3d062e2716e08b70beab4bea4676ee1394bf30a1308ac18e1c39dec6`, 309 bytes)
  - W: absent
  - P (3):
    - `materials/exploit/private/private/solve.py` ← `work/materials/pwn-v11/saj-2025-pwn-prospector/solve/private/private/solve.py` (`ec2e33e88e3b543037a109aafaf913c394133a1170c78f27a44f8099e587ac29`, 4575 bytes)
    - `materials/exploit/private/solve.sh` ← `work/materials/pwn-v11/saj-2025-pwn-prospector/solve/private/solve.sh` (`c01ad973522d4ba9138f9e7f55f93a80594c72c990be594b0f30cf7260525de1`, 167 bytes)
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2025-pwn-prospector/solve/solve.py` (`43bc3fc3dea55d60e8f7a5d680dec7350f4fd1bd846a7d1f3b7ff367d3d4b934`, 2287 bytes)
  - B (7):
    - `materials/deployment/private/private/Dockerfile` ← `work/materials/pwn-v11/saj-2025-pwn-prospector/build/private/private/Dockerfile` (`01caffa4a1730a73e6ad27510385a0cc5f9197ae1968acbd94c83b44a0be6ab1`, 278 bytes)
    - `materials/deployment/private/private/Makefile` ← `work/materials/pwn-v11/saj-2025-pwn-prospector/build/private/private/Makefile` (`b6e7c1ed2931753d25787e7f81ca0bad65b2d4de274ddedfa8d561178762ff5f`, 545 bytes)
    - `materials/deployment/private/private/libc.c` ← `work/materials/pwn-v11/saj-2025-pwn-prospector/build/private/private/libc.c` (`b7ac747dfcad1404780e8f8f88e5500d8cec3762391e8a24495aa5a8805f4bcd`, 2580 bytes)
    - `materials/deployment/private/private/libc.h` ← `work/materials/pwn-v11/saj-2025-pwn-prospector/build/private/private/libc.h` (`bb38f0c2933698d5915649290c6ee4c2cf7d8834e0357446b1f3a13175576e04`, 870 bytes)
    - `materials/deployment/private/private/prospector.c` ← `work/materials/pwn-v11/saj-2025-pwn-prospector/build/private/private/prospector.c` (`2f198c5d5f5de9a4f81ad658011398ed191826be097780464c0b2da8a2583520`, 2781 bytes)
    - `materials/deployment/private/private/run.sh` ← `work/materials/pwn-v11/saj-2025-pwn-prospector/build/private/private/run.sh` (`524cf625c4382836f6d25f7d52aa82210f7a69537bfcbccc93dbdcbb3277291c`, 31 bytes)
    - `materials/deployment/private/run.sh` ← `work/materials/pwn-v11/saj-2025-pwn-prospector/build/private/run.sh` (`2b79404f1c59b0e6ec1d98041b925b498da9a6a2daa4abb489d2c64164a12703`, 252 bytes)

### 57. `saj-2025-pwn-is-this-web` — Is_this_web

- Identity: snakeCTF / 2025 / Pwn
- Source: `MadrHacks/snakeCTF2023-Writeups`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/snakeCTF/2025/Quals/pwn/Is_this_web`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `system_libc`; `vm_emulator`
- Selection reason: adds event snakeCTF; adds source MadrHacks/snakeCTF2023-Writeups
- Material fingerprint: `424dc672bd0c6736fe9daec8a5a32c1956e6dc66a85d9a40a44ae8d54a63545e`
- Material paths:
  - A (7):
    - `materials/attachments/REVISION` ← `work/materials/pwn-v11/saj-2025-pwn-is-this-web/public/REVISION` (`768020450f6e5ae53d673ec2d41e2ab40742a89e6826b561d37740a7a6eedc1d`, 41 bytes)
    - `materials/attachments/args.gn` ← `work/materials/pwn-v11/saj-2025-pwn-is-this-web/public/args.gn` (`2bec00c20cc8ebed70076bfc377f31820e714d48f7b6329a01f9ada716416ff2`, 253 bytes)
    - `materials/attachments/d8` ← `work/materials/pwn-v11/saj-2025-pwn-is-this-web/public/d8` (`70f1cd783140555d36bcfe25dedc109561eb740d828c3efbe781c5ca570a6e97`, 66576248 bytes)
    - `materials/attachments/description.jpg` ← `work/materials/pwn-v11/saj-2025-pwn-is-this-web/public/description.jpg` (`5f3fc619e23af3722251aa3c152ec69ec315da971751ddf11c5a812465517d7e`, 63454 bytes)
    - `materials/attachments/patch` ← `work/materials/pwn-v11/saj-2025-pwn-is-this-web/public/patch` (`05550e3853c72caf5e5f75108d1d8fd492f37a626374b4234661f2d9b5b6014b`, 6476 bytes)
    - `materials/attachments/snapshot_blob.bin` ← `work/materials/pwn-v11/saj-2025-pwn-is-this-web/public/snapshot_blob.bin` (`178995bd483eee39546121e99eacd95d79c426f2010f5e7c2bfd0c453205afae`, 356686 bytes)
    - `materials/attachments/wrapper.py` ← `work/materials/pwn-v11/saj-2025-pwn-is-this-web/public/wrapper.py` (`7a6281853bb5677d1cc52503da8e865f6eb6165651795232cf26a778c45ca394`, 287 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2025-pwn-is-this-web/writeups/README.md` (`b9c0803b2d53735ec604be9b4867cfb7e3c8a4036b31c6c2ba82884735ea874f`, 10734 bytes)
  - P (2):
    - `materials/exploit/attachments/solve.js` ← `work/materials/pwn-v11/saj-2025-pwn-is-this-web/solve/attachments/solve.js` (`c97f1a9dee9ea1172f58e83c65f2beb3bde5c9b4455948e7f799af90af552fe4`, 3203 bytes)
    - `materials/exploit/attachments/solve.py` ← `work/materials/pwn-v11/saj-2025-pwn-is-this-web/solve/attachments/solve.py` (`65fa97a69156e5c397b479a3d7cf4e08467fdf220d41380d70aa0286a5ebe6bb`, 476 bytes)
  - B (3):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2025-pwn-is-this-web/build/Dockerfile` (`c19e1467092e51b9fd813ddb2601479c0ccd2491139c77b24d186b1cac7be959`, 444 bytes)
    - `materials/deployment/docker-compose.yaml` ← `work/materials/pwn-v11/saj-2025-pwn-is-this-web/build/docker-compose.yaml` (`24bebe7d267841c98af44e9cc66e2867d01546a45277c4b777c20944fd1377e6`, 201 bytes)
    - `materials/deployment/wrapper.py` ← `work/materials/pwn-v11/saj-2025-pwn-is-this-web/build/wrapper.py` (`7a6281853bb5677d1cc52503da8e865f6eb6165651795232cf26a778c45ca394`, 287 bytes)

### 58. `saj-2024-pwn-linker-as-a-service` — linker_as_a_service

- Identity: AmateursCTF / 2024 / Pwn
- Source: `les-amateurs/actf-2024-rctf`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/AmateursCTF/2024/pwn/linker_as_a_service`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `source_build`; `bundled_loader_only`; `other`
- Selection reason: adds event AmateursCTF; adds source les-amateurs/actf-2024-rctf
- Material fingerprint: `f6dd21e31bf0816e7c295e5f9f34f200c50d5b554e44eb83f9582b30c4592de9`
- Material paths:
  - A (4):
    - `materials/attachments/elf.py` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/public/elf.py` (`9098bc7863b2d428b282601042cedf472c8c58b65d50899d43f5f6864f500d38`, 32152 bytes)
    - `materials/attachments/linker-as-a-service/chal.py` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/public/linker-as-a-service/chal.py` (`188e903f6918f150958cb0b5231492100389a15657a5660028f348b5d7d8e983`, 846 bytes)
    - `materials/attachments/linker-as-a-service/elf.py` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/public/linker-as-a-service/elf.py` (`38b4a0a563a54aa1bf23fd6dc6be0f674175b16b67e235cdc04322a0f24f95ed`, 32119 bytes)
    - `materials/attachments/linker-as-a-service/ld-linux-x86-64.so.2` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/public/linker-as-a-service/ld-linux-x86-64.so.2` (`d6ca0d37e05a51dab82043f9875032331a73b468449627cbce27bc353b28ffd8`, 760888 bytes)
  - W: absent
  - P (4):
    - `materials/exploit/exploit/solve.c` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/solve/exploit/solve.c` (`bbf31ef5c9d8fa6c709b187bf27963fe5ba955bda48bceaa5db3c30b6e62247e`, 19450 bytes)
    - `materials/exploit/exploit/solve.py` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/solve/exploit/solve.py` (`c541a4fa1afbf5badb193e841ad7c0f64e6e4dce26b762dd671b456be46985be`, 598 bytes)
    - `materials/exploit/generate.py` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/solve/generate.py` (`49ae00ddddbd114b1ba38effe60d5f55e6ccb83a80e9e66f0a27981c0b39bfb8`, 661 bytes)
    - `materials/exploit/start.py` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/solve/start.py` (`6860f0e256449aa227198e673b49e243789d0c4a6415ed00f50cc916386fbc95`, 339 bytes)
  - B (16):
    - `materials/deployment/chal/Dockerfile` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/build/chal/Dockerfile` (`e71015dd17354b5dad1061f073b7c42d081d2f2c0aa9069d2e88eae36c578cf6`, 279 bytes)
    - `materials/deployment/chal/chal.py` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/build/chal/chal.py` (`188e903f6918f150958cb0b5231492100389a15657a5660028f348b5d7d8e983`, 846 bytes)
    - `materials/deployment/chal/elf.py` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/build/chal/elf.py` (`9098bc7863b2d428b282601042cedf472c8c58b65d50899d43f5f6864f500d38`, 32152 bytes)
    - `materials/deployment/exploit/Makefile` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/build/exploit/Makefile` (`f1ef89a5a647d455d1a8372e9e9ae158f6caff53cbe016efe5304cc9833bc9bf`, 422 bytes)
    - `materials/deployment/exploit/cheese/Makefile` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/build/exploit/cheese/Makefile` (`46fa9455fcc299d5833dc8a2a054934fb2dbaf7e8c882c809b277c7be5bd4618`, 160 bytes)
    - `materials/deployment/exploit/cheese/main.c` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/build/exploit/cheese/main.c` (`0b49916b3d726ecd7f0c716b4fd0406d7cb60079d70a5afec07482be6eeb548f`, 166 bytes)
    - `materials/deployment/exploit/cheese/patch.py` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/build/exploit/cheese/patch.py` (`306621329d59eea8d42152695f823562062f6d2dd0d9043a7d21b88ee14364bc`, 198 bytes)
    - `materials/deployment/exploit/cheese/test.c` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/build/exploit/cheese/test.c` (`e9b0db06412879340193f0765d4968be2afe35c07e1363d984c4dc9479ddb5b9`, 183 bytes)
    - `materials/deployment/exploit/cheese/test.py` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/build/exploit/cheese/test.py` (`e0cedb5c4982062cd5f6f386bf8d5ba1712b8ffbb60bcbab3aa086fe217f896b`, 241 bytes)
    - `materials/deployment/exploit/generate.py` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/build/exploit/generate.py` (`49ae00ddddbd114b1ba38effe60d5f55e6ccb83a80e9e66f0a27981c0b39bfb8`, 661 bytes)
    - `materials/deployment/exploit/make.sh` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/build/exploit/make.sh` (`d4623f8ea7b8cf9f726f5bf29e0a3b77c92b0f7d9a5eef535a791c6df9b7188f`, 398 bytes)
    - `materials/deployment/exploit/patch.py` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/build/exploit/patch.py` (`d8263845e14eedb4dc4a7baffc015cc317bf5566d01ac80d186835ade1740016`, 3052 bytes)
    - `materials/deployment/exploit/start.py` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/build/exploit/start.py` (`6860f0e256449aa227198e673b49e243789d0c4a6415ed00f50cc916386fbc95`, 339 bytes)
    - `materials/deployment/exploit/whatever.c` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/build/exploit/whatever.c` (`0309e74c3369542d0b73ebd8039a1ebc423a2918adc8840dfc8dd9e566ce75a0`, 8593 bytes)
    - `materials/deployment/linker-as-a-service/Dockerfile` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/build/linker-as-a-service/Dockerfile` (`7e5ace2c549053c37960a710aaae5fd410f790e5899024de0fa921540e6d207b`, 261 bytes)
    - `materials/deployment/linker-as-a-service/elf.py` ← `work/materials/pwn-v11/saj-2024-pwn-linker-as-a-service/build/linker-as-a-service/elf.py` (`38b4a0a563a54aa1bf23fd6dc6be0f674175b16b67e235cdc04322a0f24f95ed`, 32119 bytes)

### 59. `gh-d89e37825609f81e3043c42e` — snowdrop

- Identity: BeginnersCTF / 2022 / Pwn
- Source: `SECCON/Beginners_CTF_2022`; `https://github.com/SECCON/Beginners_CTF_2022/tree/4cdadd0f2bc61e2782357ad9791d4d57c70051a4/pwnable/snowdrop`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `static`; `shellcode_seccomp`, `stack_rop`
- Selection reason: adds event BeginnersCTF; adds source SECCON/Beginners_CTF_2022
- Material fingerprint: `c266a67080280376db79d38d2a4cbd4dd6b8b8f32bde603452c6663bfd89dbc8`
- Material paths:
  - A (7):
    - `materials/attachments/AAAA.png` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/public/AAAA.png` (`c56465393657746025938b9fb363a37e42b6560ac3ea9197b1eb7ffb2b322a6a`, 8337 bytes)
    - `materials/attachments/chall` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/public/chall` (`105c8fe8e5b6be7bd11c8c0e011e930bac53ac602e684291c99462bc5d747766`, 846472 bytes)
    - `materials/attachments/checksec.png` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/public/checksec.png` (`aca6350980a6e75d22788f595594916cea38bf534a4e0eff5003df8f8e346964`, 14934 bytes)
    - `materials/attachments/init.sh` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/public/init.sh` (`0435a51cba3f242f419fa005103e11ac9d87dd962c528a8714c3414085d09560`, 58 bytes)
    - `materials/attachments/redir.sh` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/public/redir.sh` (`a7f1612e0aef1c1dc995771d6fce14131ac69c4608d15434152d21d2644373a3`, 34 bytes)
    - `materials/attachments/src.c` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/public/src.c` (`649a7c6dfa83d1058a5a9142e14def4caa249d7ec2623edb6ca53a615f08c2cb`, 1072 bytes)
    - `materials/attachments/welcome.txt` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/public/welcome.txt` (`dd2c255500947fb14a6a1d48b6f923917ad62ce37a81d740a9401b374d94636d`, 275 bytes)
  - W (3):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/writeups/README.md` (`79eaa8864894a26b2d94dc622b79999607cc60290c36dbe65f832980fab366d4`, 744 bytes)
    - `materials/writeups/writeup.c7973853.md` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/writeups/writeup.c7973853.md` (`ec32cb8b13c414678184bed91c4406573b493ec8c5cb7248965747fa27f25ae1`, 821 bytes)
    - `materials/writeups/writeup.md` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/writeups/writeup.md` (`acf4df255b4b73df88630cd4bcbda5f6bf949828f6cf6f1325ba2af1e0d60426`, 295 bytes)
  - P (2):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/solve/solve.py` (`1f65e95064ad9320944523cf5dd6ad0b92ea0f16ddb4067492dd2529dd87c6b6`, 491 bytes)
    - `materials/exploit/solver/solve.py` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/solve/solver/solve.py` (`149b5af850214d4d1d5716f84c3a0b1f4b7211657ddb7b0ca941f75129040e93`, 714 bytes)
  - B (8):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/build/Dockerfile` (`8c6f514a707d2f4dad1dd32ce6f812bd7ce45c10be298b5ece41998b4fb4774d`, 648 bytes)
    - `materials/deployment/build/Dockerfile` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/build/build/Dockerfile` (`69a6172843d541cf93f2af84a73f8cacea53f2dc6ba107dd4dd742e3328e7de2`, 200 bytes)
    - `materials/deployment/build/Makefile` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/build/build/Makefile` (`0944833bee686e8178ae872dd892f4e101a6abb172fea3ebb7a9c706af032245`, 590 bytes)
    - `materials/deployment/build/init.sh` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/build/build/init.sh` (`0435a51cba3f242f419fa005103e11ac9d87dd962c528a8714c3414085d09560`, 58 bytes)
    - `materials/deployment/build/redir.sh` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/build/build/redir.sh` (`a7f1612e0aef1c1dc995771d6fce14131ac69c4608d15434152d21d2644373a3`, 34 bytes)
    - `materials/deployment/build/src.c` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/build/build/src.c` (`649a7c6dfa83d1058a5a9142e14def4caa249d7ec2623edb6ca53a615f08c2cb`, 1072 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/build/docker-compose.yml` (`9e4c5d60eaec599d7ce35886a071834c073394fe2eb1dcc1cea844392f9b6932`, 253 bytes)
    - `materials/deployment/solver/Dockerfile` ← `work/materials/pwn-v11/gh-d89e37825609f81e3043c42e/build/solver/Dockerfile` (`fa479669d59607e70d356fff5c4ef5681351edcf01abf07a448950ccc1d4a780`, 116 bytes)

### 60. `saj-2021-pwn-helpless` — Helpless

- Identity: corCTF / 2021 / Pwn
- Source: `Crusaders-of-Rust/corCTF-2021-public-challenge-archive`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/corCTF/2021/pwn/Helpless`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile_compose`; `prebuilt_rehost`; `bundled_libc_only`; `stack_rop`
- Selection reason: adds event corCTF; adds source Crusaders-of-Rust/corCTF-2021-public-challenge-archive
- Material fingerprint: `ab1597dea019d5b2532cfc89d79d7af2f19d39bc5a2bd8700e5e7b9b0119b527`
- Material paths:
  - A (3):
    - `materials/attachments/bin/ld.so` ← `work/materials/pwn-v11/saj-2021-pwn-helpless/public/bin/ld.so` (`b00432d9771264257480c5f2d7a5ae7b4c0211f6e0055beb7f150175800b6451`, 1773416 bytes)
    - `materials/attachments/bin/libc.so.6` ← `work/materials/pwn-v11/saj-2021-pwn-helpless/public/bin/libc.so.6` (`2cb87bf34b96d3f086e541e246fb1002622a95b5ccf7d50bc5272d4b41ccea18`, 19113520 bytes)
    - `materials/attachments/bin/run` ← `work/materials/pwn-v11/saj-2021-pwn-helpless/public/bin/run` (`dd392046a58de5054cec7f30b325dc741b1330aff5ac004c07f6b6d196be313b`, 25392 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/bin/exploit.py` ← `work/materials/pwn-v11/saj-2021-pwn-helpless/solve/bin/exploit.py` (`0809d534931e2bb7f037e93d416c9fac161af03f887cd8939563d38b782782bc`, 3286 bytes)
  - B (2):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2021-pwn-helpless/build/Dockerfile` (`36693e1875383fa9d5877aa4aef1953c9834370b45b13fed5a17bfca0414dc43`, 107 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/saj-2021-pwn-helpless/build/docker-compose.yml` (`8a97879f5d33bb21183da88c2e786f52f708c596f0dbe2dd9d612b5b3d009806`, 273 bytes)

### 61. `gh-6f80658fbf3ea86dafc20c5f` — pwncraft

- Identity: JeanneD Hack CTF / 2026 / Pwn
- Source: `JeanneD-Hack-CTF/JeanneD-Hack-CTF-2026`; `https://github.com/JeanneD-Hack-CTF/JeanneD-Hack-CTF-2026/tree/88e24003b9d68e005da3d1583c335fad10f3819e/pwn/pwncraft`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `source_build`; `unknown_or_non_elf`; `other`
- Selection reason: adds event JeanneD Hack CTF; adds source JeanneD-Hack-CTF/JeanneD-Hack-CTF-2026
- Material fingerprint: `577898ce57394f80a7b38e3f4e0ca010843dde34fa203f1a21eeea78b4b97bfe`
- Material paths:
  - A (27):
    - `materials/attachments/Coal.PNG` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/Coal.PNG` (`6ea61e693281ec932b81d55cf62f7d869c6a9d4db72e39a82b79f263e507ff94`, 830 bytes)
    - `materials/attachments/Diamond.PNG` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/Diamond.PNG` (`1fbf951df52f2deb6ef7cf9a952b24a9e747ed4c1d0c3f5f374fca3ec9b5828d`, 624 bytes)
    - `materials/attachments/Dirt.PNG` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/Dirt.PNG` (`1ed0ef4e82ee223405076aa9c63fa6a5237e2b67c00b388cd99ba3f2b121191a`, 695 bytes)
    - `materials/attachments/Glass.PNG` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/Glass.PNG` (`507fb786effb82c8cf162aa4350347daad72a4ef846f8973994c02229373755d`, 573 bytes)
    - `materials/attachments/Gold.PNG` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/Gold.PNG` (`544d09923ff003149862e1422df359e68c5b234a0c768cfc539423888f2a73b2`, 832 bytes)
    - `materials/attachments/Grass.PNG` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/Grass.PNG` (`ad85380c1dfa68f3baf4d7db999b9e057f2b52707334c2965458049a9c73c188`, 755 bytes)
    - `materials/attachments/Leaves.PNG` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/Leaves.PNG` (`d0a56d42afcc75c44d08d202f887fd70d66449361dfaae4220d3e4d9461d5570`, 681 bytes)
    - `materials/attachments/Redstone.PNG` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/Redstone.PNG` (`60234910e4de9cf403934b80d1fb7c0251482d08e258397fbd40206360cde66f`, 832 bytes)
    - `materials/attachments/Sand.PNG` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/Sand.PNG` (`9c6e6aa57604ba7daa991a5fb9e3d7156869fc08a6c0ff626ac51ed964b8e389`, 709 bytes)
    - `materials/attachments/Spritesheet.PNG` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/Spritesheet.PNG` (`024fa0334cbf5cad6204f8f73544eeaae0f66cff422c9b88b0aa994f8555183c`, 12179 bytes)
    - `materials/attachments/Stone.PNG` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/Stone.PNG` (`926cb4c152430f5bcb91ecd51864b83fc5c3b8f92d1a3a8741664833d38d82f4`, 689 bytes)
    - `materials/attachments/Tnt.PNG` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/Tnt.PNG` (`1b5eb6a2f525c8da6af9cf3d31667a7d3b6dafe86c6e6ffff9f53efa6dfe9e33`, 599 bytes)
    - `materials/attachments/Water.PNG` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/Water.PNG` (`5e2192c1ee58cc1275aa84d4da1378568afde8cd1c4983ba0b6960519b7c7ad5`, 757 bytes)
    - `materials/attachments/client.c` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/client.c` (`4605bfa7fd136a0e103058ae62756b61308a7349c6b6a723df3a52759188006a`, 6181 bytes)
    - `materials/attachments/client.h` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/client.h` (`8178fc41f88d81367ff70692a8a500620460bbded9b26334198c99682c259e49`, 480 bytes)
    - `materials/attachments/frame.c` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/frame.c` (`b6080480af61b008fd72ec179685dac39d9ec72d467c8fa91ca4664ea6fa95ee`, 5332 bytes)
    - `materials/attachments/frame.h` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/frame.h` (`43a2b290ba8c77654cd3aea5d9085b68cfaf1e2efa73e63d737c2cade2c63d16`, 973 bytes)
    - `materials/attachments/game.js` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/game.js` (`018fb477b3a78854cee17871ebf9860f378a9946a7777e96e2174982f244a643`, 8583 bytes)
    - `materials/attachments/main.c` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/main.c` (`ca758b73a79c8f407b6c059ca0526658288fac91860dd97c5c30947052336d4d`, 15383 bytes)
    - `materials/attachments/pwncraft.PNG` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/pwncraft.PNG` (`fbfdbe766cca579139e45f2fc3b650ea6bdb4b825b987e3e14596b1cf19c087a`, 24575 bytes)
    - `materials/attachments/sha1.c` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/sha1.c` (`82abd0ceb2c2da9c363462a570635ad9dd74ef09337c242ad89b2439e900a8ce`, 2436 bytes)
    - `materials/attachments/sha1.h` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/sha1.h` (`fedd9e1f14aaab9fc246edea5489ed0836f562b7dd200c6add56d8cc2d1f47b5`, 442 bytes)
    - `materials/attachments/steve.PNG` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/steve.PNG` (`c17d32a0e57b5e489e4093dae5dbea6758b64f3daba8502042a0cbea3628a9d5`, 42497 bytes)
    - `materials/attachments/wood.PNG` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/wood.PNG` (`b45aa56edbf221beba2cb3d727274215e67775317a1d65d5ea4f49c1aeb10e89`, 635 bytes)
    - `materials/attachments/ws.c` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/ws.c` (`c391ea0f973f5c92ce59ef7241145d6bb6be655c4b3e7532d69f65f0c7ea6e26`, 10740 bytes)
    - `materials/attachments/ws.h` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/ws.h` (`a8f055cc6f89a0fb01ea34ee5908a7a322ee9a57d8defc42bfe5c8232c322ef4`, 554 bytes)
    - `materials/attachments/wsClient.js` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/public/wsClient.js` (`8245d959339b47ef3180083ce5e7b5cb9330c344c2418a7dd6394c2a77244c65`, 6916 bytes)
  - W (1):
    - `materials/writeups/pwn-writeup-2026-edition-jeanne-d-hack-ctf.html` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/writeups/pwn-writeup-2026-edition-jeanne-d-hack-ctf.html` (`2ac85965ca8132d7fe60599f1cb382b46f325b08f052342f1f33d6eef23fff04`, 177433 bytes)
  - P (1):
    - `materials/exploit/poc.py` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/solve/poc.py` (`72e89231ee9e294ca781cdefac2cbb6a20cf6bbe45e8e646da405eeddab4359e`, 10279 bytes)
  - B (16):
    - `materials/deployment/build.sh` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/build/build.sh` (`0eb918e4110803efb11790c5138811fdce83d54d83f1f01081f26d7d77862f13`, 144 bytes)
    - `materials/deployment/client/Dockerfile` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/build/client/Dockerfile` (`554fb3b9ae0a7ea3fcaee35e0181f2134561a8f95e0c3a672dca147ec9c038c7`, 302 bytes)
    - `materials/deployment/client/game.js` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/build/client/game.js` (`018fb477b3a78854cee17871ebf9860f378a9946a7777e96e2174982f244a643`, 8583 bytes)
    - `materials/deployment/client/wsClient.js` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/build/client/wsClient.js` (`8245d959339b47ef3180083ce5e7b5cb9330c344c2418a7dd6394c2a77244c65`, 6916 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/build/docker-compose.yml` (`781639d050a86f5df235e73efd11dd4a1e51a7df3e6ed72b2cbbf95f39f618a7`, 352 bytes)
    - `materials/deployment/server/Dockerfile` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/build/server/Dockerfile` (`9495ad67be6b14da35057cd1bb6de20a5c9b1cc3ff0e235be4fa2419d1993608`, 925 bytes)
    - `materials/deployment/server/Makefile` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/build/server/Makefile` (`b7f9984a4f850f1924d433e04490a37429778aa813952298acdddfae7eb13380`, 379 bytes)
    - `materials/deployment/server/client.c` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/build/server/client.c` (`4605bfa7fd136a0e103058ae62756b61308a7349c6b6a723df3a52759188006a`, 6181 bytes)
    - `materials/deployment/server/client.h` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/build/server/client.h` (`8178fc41f88d81367ff70692a8a500620460bbded9b26334198c99682c259e49`, 480 bytes)
    - `materials/deployment/server/frame.c` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/build/server/frame.c` (`b6080480af61b008fd72ec179685dac39d9ec72d467c8fa91ca4664ea6fa95ee`, 5332 bytes)
    - `materials/deployment/server/frame.h` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/build/server/frame.h` (`43a2b290ba8c77654cd3aea5d9085b68cfaf1e2efa73e63d737c2cade2c63d16`, 973 bytes)
    - `materials/deployment/server/main.c` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/build/server/main.c` (`ca758b73a79c8f407b6c059ca0526658288fac91860dd97c5c30947052336d4d`, 15383 bytes)
    - `materials/deployment/server/sha1.c` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/build/server/sha1.c` (`82abd0ceb2c2da9c363462a570635ad9dd74ef09337c242ad89b2439e900a8ce`, 2436 bytes)
    - `materials/deployment/server/sha1.h` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/build/server/sha1.h` (`fedd9e1f14aaab9fc246edea5489ed0836f562b7dd200c6add56d8cc2d1f47b5`, 442 bytes)
    - `materials/deployment/server/ws.c` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/build/server/ws.c` (`c391ea0f973f5c92ce59ef7241145d6bb6be655c4b3e7532d69f65f0c7ea6e26`, 10740 bytes)
    - `materials/deployment/server/ws.h` ← `work/materials/pwn-v11/gh-6f80658fbf3ea86dafc20c5f/build/server/ws.h` (`a8f055cc6f89a0fb01ea34ee5908a7a322ee9a57d8defc42bfe5c8232c322ef4`, 554 bytes)

### 62. `saj-2024-pwn-directory` — Directory

- Identity: BYUCTF / 2024 / Pwn
- Source: `BYU-CSA/BYUCTF-2024`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/BYUCTF/2024/pwn/Directory`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `system_libc`; `other`
- Selection reason: adds event BYUCTF; adds source BYU-CSA/BYUCTF-2024
- Material fingerprint: `d68d48ee86ca893be929eebe8194451a6a36d3c2bc0dfa4766aec919e3dbb34f`
- Material paths:
  - A (3):
    - `materials/attachments/ctf.xinetd` ← `work/materials/pwn-v11/saj-2024-pwn-directory/public/ctf.xinetd` (`c660a2ad39d6057e58f11fe09281a77a3dd3a6cf336a09c153f14f505133885c`, 495 bytes)
    - `materials/attachments/directory.c` ← `work/materials/pwn-v11/saj-2024-pwn-directory/public/directory.c` (`d492c801eb24b67c4f4e246b8324437812357062f96c76b645fda26138baf657`, 2463 bytes)
    - `materials/attachments/src/directory` ← `work/materials/pwn-v11/saj-2024-pwn-directory/public/src/directory` (`7e32d2b30e32e2dd391c092d06bf757f28ba9d81cbe03f4f182d15c5c1aea2a8`, 16632 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2024-pwn-directory/solve/solve.py` (`53ad976d1993f5cfdbc81ef4a9d2d8f29a5f3c121c4b033261ed569d8a033396`, 624 bytes)
  - B (5):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2024-pwn-directory/build/Dockerfile` (`5dbf1f69d804e1c1d8f65c36f8d10a3373bf3a2d6e00dcdefcb0092950a4d3b5`, 460 bytes)
    - `materials/deployment/directory.c` ← `work/materials/pwn-v11/saj-2024-pwn-directory/build/directory.c` (`d492c801eb24b67c4f4e246b8324437812357062f96c76b645fda26138baf657`, 2463 bytes)
    - `materials/deployment/docker-compose.ed1bded1.yml` ← `work/materials/pwn-v11/saj-2024-pwn-directory/build/docker-compose.ed1bded1.yml` (`4b27dc988ade7fb85c19312564ad3981b388fe181f54784e084641acee21533e`, 112 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/saj-2024-pwn-directory/build/docker-compose.yml` (`743796800f95be078baf9bf1ba93fdf26cf8de771761524f34a9e9af420e7d52`, 111 bytes)
    - `materials/deployment/src/start.sh` ← `work/materials/pwn-v11/saj-2024-pwn-directory/build/src/start.sh` (`b42ef37e477467cc1185e0e972ff0f66c65a9ca075fd983a3c1d4f8d2949e575`, 31 bytes)

### 63. `saj-2025-pwn-haatetepe` — haatetepe

- Identity: NNS / 2025 / Pwn
- Source: `Norske-Nokkelsnikere/nns-ctf-2025`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/NNS/2025/pwn/haatetepe`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `static`; `stack_rop`
- Selection reason: adds event NNS; adds source Norske-Nokkelsnikere/nns-ctf-2025
- Material fingerprint: `262f6630c19aef4bb242e31e82617821dd36a95b5b0e6477b94349b06cf94b60`
- Material paths:
  - A (3):
    - `materials/attachments/haatetepe/haatetepe` ← `work/materials/pwn-v11/saj-2025-pwn-haatetepe/public/haatetepe/haatetepe` (`3de97ded5c4a82bbaea986e068bec2fa431e85ec37beb679a5edc2057289ed15`, 882824 bytes)
    - `materials/attachments/haatetepe/main.c` ← `work/materials/pwn-v11/saj-2025-pwn-haatetepe/public/haatetepe/main.c` (`894aedec69f1a49cade240e1f2f4974ad157a2f3f77f5c597901dbdefb0eb3d6`, 8394 bytes)
    - `materials/attachments/main.c` ← `work/materials/pwn-v11/saj-2025-pwn-haatetepe/public/main.c` (`e4af28cfa6f167a04c455997d1c3a15284a3a70c300b96235524c3d362905454`, 8423 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2025-pwn-haatetepe/writeups/README.md` (`5955aea1253f996599601df74dbc5d56a135923a783d6969926e9cbafb47fda3`, 1766 bytes)
  - P (2):
    - `materials/exploit/exp.py` ← `work/materials/pwn-v11/saj-2025-pwn-haatetepe/solve/exp.py` (`65236ff3e12fc6047d18db634511bc686653e4f29d17801911bff005d56e68e2`, 2108 bytes)
    - `materials/exploit/writeup/solve.py` ← `work/materials/pwn-v11/saj-2025-pwn-haatetepe/solve/writeup/solve.py` (`6dd170ff91d36f68d9a7d5f31025622a00f47362a7cf88590598210f5f4b0951`, 163 bytes)
  - B (3):
    - `materials/deployment/src/Dockerfile` ← `work/materials/pwn-v11/saj-2025-pwn-haatetepe/build/src/Dockerfile` (`69d42dad798729128c5d151cf2f592c1f2d6648874acde2e3d8d8bfcce1118c1`, 98 bytes)
    - `materials/deployment/src/Makefile` ← `work/materials/pwn-v11/saj-2025-pwn-haatetepe/build/src/Makefile` (`6a66f5673d36a51f2196f5078d792d7fca4e48dd8f69df40af65f05ae4af3ef5`, 68 bytes)
    - `materials/deployment/src/main.c` ← `work/materials/pwn-v11/saj-2025-pwn-haatetepe/build/src/main.c` (`894aedec69f1a49cade240e1f2f4974ad157a2f3f77f5c597901dbdefb0eb3d6`, 8394 bytes)

### 64. `saj-2021-pwn-coffeeshop` — CoffeeShop

- Identity: idekCTF / 2021 / Pwn
- Source: `idekctf/idekctf-2021`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/idekCTF/2021/pwn/CoffeeShop`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `bundled_libc_loader`; `heap`
- Selection reason: adds event idekCTF; adds source idekctf/idekctf-2021
- Material fingerprint: `f9569032723d556a0c870c834a157d08ace928a6a6a05867e0a0dfb48f13bffe`
- Material paths:
  - A (6):
    - `materials/attachments/challenge.yaml` ← `work/materials/pwn-v11/saj-2021-pwn-coffeeshop/public/challenge.yaml` (`df912ce4046f9c92bd61e23b23fc4df5f52587f6a4e9692c66e5972b85aa623b`, 466 bytes)
    - `materials/attachments/coffee_shop` ← `work/materials/pwn-v11/saj-2021-pwn-coffeeshop/public/coffee_shop` (`06ad01f56c289dc981edb0071ed107bfb83e63ad501b9c5eae3bd861ccb13286`, 17632 bytes)
    - `materials/attachments/coffee_shop.c` ← `work/materials/pwn-v11/saj-2021-pwn-coffeeshop/public/coffee_shop.c` (`73b542a82b4b533926d010741fa3b986a3afe9718c7852c58b2d20a5cabaa07d`, 4396 bytes)
    - `materials/attachments/coffee_shop_patched` ← `work/materials/pwn-v11/saj-2021-pwn-coffeeshop/public/coffee_shop_patched` (`15204970bae05e029c262d0bb2e6bbbf42c492f2b07526473f5a5a2a0fa4f6e3`, 21816 bytes)
    - `materials/attachments/ld-2.31.so` ← `work/materials/pwn-v11/saj-2021-pwn-coffeeshop/public/ld-2.31.so` (`0a96b6c36729ebdc85b18e2bf036b1a1b4bd96e3c593c31b5154c3a1d15bda2f`, 177928 bytes)
    - `materials/attachments/libc-2.31.so` ← `work/materials/pwn-v11/saj-2021-pwn-coffeeshop/public/libc-2.31.so` (`4db473e38da06f7b1ad54ef117a184e08ffda27bbbb5329d03831186e3e533c8`, 2029224 bytes)
  - W: absent
  - P (2):
    - `materials/exploit/exploit.48fbe20a.py` ← `work/materials/pwn-v11/saj-2021-pwn-coffeeshop/solve/exploit.48fbe20a.py` (`38e52d69c1111da0993d7dd4ca575ef672bf580da3447988cd5a8e9b9a7d8a10`, 815 bytes)
    - `materials/exploit/exploit.py` ← `work/materials/pwn-v11/saj-2021-pwn-coffeeshop/solve/exploit.py` (`d352488d1e9e5b834c1c29ae959df0dd105bdbc4b9eddf63056a982302becd34`, 1841 bytes)
  - B (7):
    - `materials/deployment/challenge/Dockerfile` ← `work/materials/pwn-v11/saj-2021-pwn-coffeeshop/build/challenge/Dockerfile` (`b045c561ac1714cc1656cc8cd789a0f1184d1b133204edb5ed169596f035ecb9`, 1064 bytes)
    - `materials/deployment/challenge/Makefile` ← `work/materials/pwn-v11/saj-2021-pwn-coffeeshop/build/challenge/Makefile` (`a5e4e5627e43009ace8ebb2a2febb8b78ef6075d9d69c4183e297a34bdedc4d8`, 38 bytes)
    - `materials/deployment/challenge/coffee_shop.c` ← `work/materials/pwn-v11/saj-2021-pwn-coffeeshop/build/challenge/coffee_shop.c` (`73b542a82b4b533926d010741fa3b986a3afe9718c7852c58b2d20a5cabaa07d`, 4396 bytes)
    - `materials/deployment/healthcheck/Dockerfile` ← `work/materials/pwn-v11/saj-2021-pwn-coffeeshop/build/healthcheck/Dockerfile` (`592b91dbb6dc00ac3f5081a78b29e2e41ab77f012a42a769cf80aee144f57115`, 984 bytes)
    - `materials/deployment/healthcheck/healthcheck.py` ← `work/materials/pwn-v11/saj-2021-pwn-coffeeshop/build/healthcheck/healthcheck.py` (`40adc06c09dbe3871a8eec2bc9116d78db8d22a180217c92fee941c972e3592a`, 2925 bytes)
    - `materials/deployment/healthcheck/healthcheck_loop.sh` ← `work/materials/pwn-v11/saj-2021-pwn-coffeeshop/build/healthcheck/healthcheck_loop.sh` (`f26fd678c224089b30c7a8049d96d42883344be9e998f80bc02e8676d63e1ce5`, 896 bytes)
    - `materials/deployment/healthcheck/healthz_webserver.py` ← `work/materials/pwn-v11/saj-2021-pwn-coffeeshop/build/healthcheck/healthz_webserver.py` (`50810e810d849d2a451a223402297d8b777794ef028b601e22447e23604ea56a`, 1388 bytes)

### 65. `saj-2020-na-skywriting` — skywriting

- Identity: redpwn / 2020 / Pwn
- Source: `redpwn/redpwnctf-2021-challenges`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/redpwn/2020/skywriting`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `bundled_libc_only`; `stack_rop`
- Selection reason: adds event redpwn; adds source redpwn/redpwnctf-2021-challenges
- Material fingerprint: `d1e564785680d2029952cdbbf02c2297f62ec390c6e963b2e42d6bb635ae4cd0`
- Material paths:
  - A (7):
    - `materials/attachments/bin/skywriting` ← `work/materials/pwn-v11/saj-2020-na-skywriting/public/bin/skywriting` (`7cc34af1554474ba83298f46d706f52be9b9545f33c7a1100458c01b0ff58706`, 10224 bytes)
    - `materials/attachments/ctf.xinetd` ← `work/materials/pwn-v11/saj-2020-na-skywriting/public/ctf.xinetd` (`576fbcc40f76ad128d09676dc5d3e53a2e1bceeaeb2aa545eb6adea4e672746f`, 594 bytes)
    - `materials/attachments/docker.sh` ← `work/materials/pwn-v11/saj-2020-na-skywriting/public/docker.sh` (`096f5d0bc76b5c3f97dcc8312d0f222092828badcf16713846176d319e05f123`, 177 bytes)
    - `materials/attachments/libc.so.6` ← `work/materials/pwn-v11/saj-2020-na-skywriting/public/libc.so.6` (`cd7c1a035d24122798d97a47a10f6e2b71d58710aecfd392375f1aa9bdde164d`, 2030544 bytes)
    - `materials/attachments/main.png` ← `work/materials/pwn-v11/saj-2020-na-skywriting/public/main.png` (`9fb7c296146d84b3a720c60147a203b8b0c7117ab874182d44c14705d5a21f09`, 354447 bytes)
    - `materials/attachments/readme.txt` ← `work/materials/pwn-v11/saj-2020-na-skywriting/public/readme.txt` (`afbcbd563603e7516b18d4fe796e5e39e879754622e1ce45682dbc7eff4f4c58`, 171 bytes)
    - `materials/attachments/skywriting.c` ← `work/materials/pwn-v11/saj-2020-na-skywriting/public/skywriting.c` (`bfa9147858cd8943eea9b35b1f09b25a75eb9e9d80698d5bff0809261e047547`, 1180 bytes)
  - W (2):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2020-na-skywriting/writeups/README.md` (`178a91bbbf46743b2572ed85a0ee0186628899dc29928ac9c5d9aca9ed9e0de8`, 5768 bytes)
    - `materials/writeups/Skywriting.md` ← `work/materials/pwn-v11/saj-2020-na-skywriting/writeups/Skywriting.md` (`183cfad46f71972ee7dd17ba392ae5ea4029cd654be0299e6e20092ca0382090`, 4947 bytes)
  - P (4):
    - `materials/exploit/exploit.241faee8.py` ← `work/materials/pwn-v11/saj-2020-na-skywriting/solve/exploit.241faee8.py` (`a8e3466fa450305454b5a4d59a8dbd39d5a5999c26eb73d4e6d6d708a2a89a0a`, 1254 bytes)
    - `materials/exploit/exploit.py` ← `work/materials/pwn-v11/saj-2020-na-skywriting/solve/exploit.py` (`54b151dfaff3f0bb01cb2cdbbb62db2d6e322f58dfc6510f0f14fb16cbcf891f`, 1117 bytes)
    - `materials/exploit/solve.d0d73d1b.py` ← `work/materials/pwn-v11/saj-2020-na-skywriting/solve/solve.d0d73d1b.py` (`dbd402e0959bb177d7c77b22ccaa7ef54c171ec456db86c834f1e3e9651f014b`, 1206 bytes)
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2020-na-skywriting/solve/solve.py` (`235823deaa1ee5bfddf9df03d97090df837156ec03388d544e2a551bc53f7c2a`, 755 bytes)
  - B (4):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2020-na-skywriting/build/Dockerfile` (`c0e92802de512c22bc5077ea5a067282674f17947eabaa2038f9bd7c1512559b`, 869 bytes)
    - `materials/deployment/bin/Makefile` ← `work/materials/pwn-v11/saj-2020-na-skywriting/build/bin/Makefile` (`3f87d448c14a38340edd3ecab3ea20e37330a8ceeb94fe709ade79295e73d9db`, 67 bytes)
    - `materials/deployment/bin/skywriting.c` ← `work/materials/pwn-v11/saj-2020-na-skywriting/build/bin/skywriting.c` (`bfa9147858cd8943eea9b35b1f09b25a75eb9e9d80698d5bff0809261e047547`, 1180 bytes)
    - `materials/deployment/start.sh` ← `work/materials/pwn-v11/saj-2020-na-skywriting/build/start.sh` (`3197e89b05525ebb9d76bad1d14cf124f88ec8647fd475a013b757ab6614a46d`, 96 bytes)

### 66. `saj-2023-pwn-you-want-me-to-run-what` — You_Want_Me_To_Run_What

- Identity: UMDCTF / 2023 / Pwn
- Source: `UMD-CSEC/UMDCTF-Public-Challenges`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/UMDCTF/2023/pwn/You_Want_Me_To_Run_What`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `static`; `other`
- Selection reason: adds event UMDCTF; adds source UMD-CSEC/UMDCTF-Public-Challenges
- Material fingerprint: `676ba8f962e09ee556fa9774568fcf4fa99105bf7d9f969dab8dc7155c111c33`
- Material paths:
  - A (8):
    - `materials/attachments/GoReSym` ← `work/materials/pwn-v11/saj-2023-pwn-you-want-me-to-run-what/public/GoReSym` (`7e3102cbebd3ec523cee55ffe94cb6ba95961842d528ee2fb169aae3b602f2e0`, 4485863 bytes)
    - `materials/attachments/build-docker.sh` ← `work/materials/pwn-v11/saj-2023-pwn-you-want-me-to-run-what/public/build-docker.sh` (`62e46f4331a324a116dc2db004c2dc473a0537fcbecad004c5e591a87f6c4b5e`, 48 bytes)
    - `materials/attachments/gen.go` ← `work/materials/pwn-v11/saj-2023-pwn-you-want-me-to-run-what/public/gen.go` (`c0a95a0bc0b8ae627e543597816cd541aad9da40e8dcdc13937bf35c9fe61515`, 1009 bytes)
    - `materials/attachments/md5test.py` ← `work/materials/pwn-v11/saj-2023-pwn-you-want-me-to-run-what/public/md5test.py` (`77c598e9dcb38af0f83044073f6e5dc499993e6f5254aed0d33c42438279a821`, 2008 bytes)
    - `materials/attachments/run-docker.sh` ← `work/materials/pwn-v11/saj-2023-pwn-you-want-me-to-run-what/public/run-docker.sh` (`8557187bd9e9ec11259a35fd52e514a02925d01b8b1b97143cac5b73d646e791`, 64 bytes)
    - `materials/attachments/run.go` ← `work/materials/pwn-v11/saj-2023-pwn-you-want-me-to-run-what/public/run.go` (`5be95a7c6e97ccf1121d5ec7ab26799c95b28ee0314a4bc31e617765032abcb6`, 3957 bytes)
    - `materials/attachments/youwantmetorunwhat` ← `work/materials/pwn-v11/saj-2023-pwn-you-want-me-to-run-what/public/youwantmetorunwhat` (`0e1eff74da246a3a8177e4fd920d268dfff0d9bb13b4343484c043a3d0990372`, 1840632 bytes)
    - `materials/attachments/youwantmetorunwhat.remote` ← `work/materials/pwn-v11/saj-2023-pwn-you-want-me-to-run-what/public/youwantmetorunwhat.remote` (`3ab5351c9d6a98f926188f67f8f8fa206ca09a6072d1d946d73fb6ba49f0e307`, 2701008 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/exploit.py` ← `work/materials/pwn-v11/saj-2023-pwn-you-want-me-to-run-what/solve/exploit.py` (`162e3927b2a28afb5adea4341ecc64f064a99e43d74afcc2f735390509e82e00`, 1927 bytes)
  - B (6):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2023-pwn-you-want-me-to-run-what/build/Dockerfile` (`c19b9dba1681a90d680864bc63b598309714e7c9e7138491e7b272e265f0b9fb`, 147 bytes)
    - `materials/deployment/build-docker.sh` ← `work/materials/pwn-v11/saj-2023-pwn-you-want-me-to-run-what/build/build-docker.sh` (`62e46f4331a324a116dc2db004c2dc473a0537fcbecad004c5e591a87f6c4b5e`, 48 bytes)
    - `materials/deployment/gen.go` ← `work/materials/pwn-v11/saj-2023-pwn-you-want-me-to-run-what/build/gen.go` (`c0a95a0bc0b8ae627e543597816cd541aad9da40e8dcdc13937bf35c9fe61515`, 1009 bytes)
    - `materials/deployment/run-docker.sh` ← `work/materials/pwn-v11/saj-2023-pwn-you-want-me-to-run-what/build/run-docker.sh` (`8557187bd9e9ec11259a35fd52e514a02925d01b8b1b97143cac5b73d646e791`, 64 bytes)
    - `materials/deployment/run.go` ← `work/materials/pwn-v11/saj-2023-pwn-you-want-me-to-run-what/build/run.go` (`5be95a7c6e97ccf1121d5ec7ab26799c95b28ee0314a4bc31e617765032abcb6`, 3957 bytes)
    - `materials/deployment/run.sh` ← `work/materials/pwn-v11/saj-2023-pwn-you-want-me-to-run-what/build/run.sh` (`1ebe40bf43427588a4b7d305547cba9585ff318256a3d5b6775ccb89bf3faa12`, 65 bytes)

### 67. `gh-cecbb796f52e3898df80d06e` — ret ftw

- Identity: BtS CTF 03 / 2021 / Pwn
- Source: `PWrWhiteHats/BtS-CTF-Challenges-03-2021`; `https://github.com/PWrWhiteHats/BtS-CTF-Challenges-03-2021/tree/545880c414a6c55fe216d71f9eee2f54f64bb070/pwn/ret_ftw`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `system_libc`; `other`
- Selection reason: adds event BtS CTF 03; adds source PWrWhiteHats/BtS-CTF-Challenges-03-2021
- Material fingerprint: `0d2254176dd90ef2d596f939d2c49dd0a0634f1ad751a780ec25520d316eb063`
- Material paths:
  - A (3):
    - `materials/attachments/for_player` ← `work/materials/pwn-v11/gh-cecbb796f52e3898df80d06e/public/for_player` (`3529c5ccb987025958834aaa00a624c037013bcc13abe3f6e01d0f558926bacc`, 17072 bytes)
    - `materials/attachments/for_player.c` ← `work/materials/pwn-v11/gh-cecbb796f52e3898df80d06e/public/for_player.c` (`063c0d7c51ae72eb8e33ebcc5aff47a954f401c9b7a41727354480cc26d34491`, 396 bytes)
    - `materials/attachments/for_server.c` ← `work/materials/pwn-v11/gh-cecbb796f52e3898df80d06e/public/for_server.c` (`ba96295bf8eae0e3911e405fcea0e71f6df610e2ffd913b3ca856b490f79466c`, 396 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/gh-cecbb796f52e3898df80d06e/writeups/README.md` (`bbb780ef27f273484586fdbbcaefa34aa3d0c1160dfae9a220bcbac3d10940c3`, 104 bytes)
  - P (1):
    - `materials/exploit/retftw.py` ← `work/materials/pwn-v11/gh-cecbb796f52e3898df80d06e/solve/retftw.py` (`0fa9777af2e46440b222f241b4ed548ca05a854d9cc36157cb085548596f0705`, 147 bytes)
  - B (4):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-cecbb796f52e3898df80d06e/build/Dockerfile` (`49f9045da13579b35cf37d0503b156b90cea65328b3c8867c47f0e3055d1b56a`, 541 bytes)
    - `materials/deployment/for_player.c` ← `work/materials/pwn-v11/gh-cecbb796f52e3898df80d06e/build/for_player.c` (`063c0d7c51ae72eb8e33ebcc5aff47a954f401c9b7a41727354480cc26d34491`, 396 bytes)
    - `materials/deployment/for_server.c` ← `work/materials/pwn-v11/gh-cecbb796f52e3898df80d06e/build/for_server.c` (`ba96295bf8eae0e3911e405fcea0e71f6df610e2ffd913b3ca856b490f79466c`, 396 bytes)
    - `materials/deployment/solution/retftw.py` ← `work/materials/pwn-v11/gh-cecbb796f52e3898df80d06e/build/solution/retftw.py` (`0fa9777af2e46440b222f241b4ed548ca05a854d9cc36157cb085548596f0705`, 147 bytes)

### 68. `saj-2022-pwn-warmup2` — warmup2

- Identity: MapleCTF / 2022 / Pwn
- Source: `ubcctf/sapling-ctf-2022`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/MapleCTF/2022/pwn/warmup2`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `bundled_libc_only`; `format_string`, `stack_rop`
- Selection reason: adds event MapleCTF; adds source ubcctf/sapling-ctf-2022
- Material fingerprint: `0a8bbcc6fdd5fb2b787c822d21fe2bd7a6e716cca99a8c271baec12afdf0577c`
- Material paths:
  - A (5):
    - `materials/attachments/chal` ← `work/materials/pwn-v11/saj-2022-pwn-warmup2/public/chal` (`5b45479a2f8469d6fc7c46108b0109bac10318866c2780dfd512706fd82e578e`, 17040 bytes)
    - `materials/attachments/challenge.sh` ← `work/materials/pwn-v11/saj-2022-pwn-warmup2/public/challenge.sh` (`e653d2fc7f1ab1df7f3d465b15ac305972c52b6b280e99ce199a3265a2b1087c`, 31 bytes)
    - `materials/attachments/libc-2.31.so` ← `work/materials/pwn-v11/saj-2022-pwn-warmup2/public/libc-2.31.so` (`80378c2017456829f32645e6a8f33b4c40c8efa87db7e8c931a229afa7bf6712`, 2029592 bytes)
    - `materials/attachments/libc6-i386_2.31-13_amd64.so` ← `work/materials/pwn-v11/saj-2022-pwn-warmup2/public/libc6-i386_2.31-13_amd64.so` (`7cbfa1d98165845b073b363a9c51ed5cceea488757fb164fad45642854f08803`, 1993968 bytes)
    - `materials/attachments/warmup2.py` ← `work/materials/pwn-v11/saj-2022-pwn-warmup2/public/warmup2.py` (`20d99a8770e427a9998c7abf0ce5eb5019138344e87c01185a3f8f645aa1328a`, 993 bytes)
  - W: absent
  - P (3):
    - `materials/exploit/exploit.88892158.py` ← `work/materials/pwn-v11/saj-2022-pwn-warmup2/solve/exploit.88892158.py` (`ac4fec50885f26114386c742f9dba3ac96ebc1c5e681f793676ba2ccaf0eb86a`, 2163 bytes)
    - `materials/exploit/exploit.py` ← `work/materials/pwn-v11/saj-2022-pwn-warmup2/solve/exploit.py` (`a47c3088660b31a961ef22d454d4310d566f453edb4b4e058e57c19bd71b2ebc`, 2645 bytes)
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2022-pwn-warmup2/solve/solve.py` (`a4efbb0743451876e0f68591ca24fc1d1f66b2c7168943029806da4e0e5d6a4d`, 904 bytes)
  - B (2):
    - `materials/deployment/hosted/Dockerfile` ← `work/materials/pwn-v11/saj-2022-pwn-warmup2/build/hosted/Dockerfile` (`450cc7ede073ad484f6cbf583cc960f84e3805d194cb4bec4b2c9e0c1a887edc`, 249 bytes)
    - `materials/deployment/hosted/challenge.sh` ← `work/materials/pwn-v11/saj-2022-pwn-warmup2/build/hosted/challenge.sh` (`e653d2fc7f1ab1df7f3d465b15ac305972c52b6b280e99ce199a3265a2b1087c`, 31 bytes)

### 69. `saj-2023-pwn-strings` — Strings

- Identity: n00bzCTF / 2023 / Pwn
- Source: `n00bzUnit3d/n00bzCTF2024-Official-Writeups`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/n00bzCTF/2023/pwn/Strings`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `system_libc`; `format_string`
- Selection reason: adds event n00bzCTF; adds source n00bzUnit3d/n00bzCTF2024-Official-Writeups
- Material fingerprint: `d38e00592f4dd0ba956ecf29e41552f2103c9eb7ef3fc1899ecedb3271cdc516`
- Material paths:
  - A (3):
    - `materials/attachments/chall.c` ← `work/materials/pwn-v11/saj-2023-pwn-strings/public/chall.c` (`9a9a0472fbb8285da2b55980b3d7bc776b856fe47e4f93db1f70f3e92cc04430`, 546 bytes)
    - `materials/attachments/strings` ← `work/materials/pwn-v11/saj-2023-pwn-strings/public/strings` (`d6f8d0ae40a7e9b14fdbfa09041d27141262ecbc15363b5c4172e7996f7b3f80`, 16392 bytes)
    - `materials/attachments/strings.py` ← `work/materials/pwn-v11/saj-2023-pwn-strings/public/strings.py` (`18ddad2894341321b7ae87e2e438c41951895b5418393cf01c05aa6d5ff742df`, 1807 bytes)
  - W (4):
    - `materials/writeups/README.a897de6e.md` ← `work/materials/pwn-v11/saj-2023-pwn-strings/writeups/README.a897de6e.md` (`33f8b47d91fc5ad21c5e9def176f95b2259f561a63ccf7ac6abac81e4a9aabfa`, 481 bytes)
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2023-pwn-strings/writeups/README.md` (`6dc7becf10dd81f430cc37a0ca32e38d31c19fb7609286918ff1e961397842e7`, 3081 bytes)
    - `materials/writeups/local-community-wp-f3cc7c5682dcefe35f20acff.md` ← `work/materials/pwn-v11/saj-2023-pwn-strings/writeups/local-community-wp-f3cc7c5682dcefe35f20acff.md` (`8b2b49ae9a9fc845b8bb3e9d6357a5828aa792511bdc27e21530bfd609a7c109`, 11090 bytes)
    - `materials/writeups/n00bzCTF-2023.md` ← `work/materials/pwn-v11/saj-2023-pwn-strings/writeups/n00bzCTF-2023.md` (`33091fad7cfa9e707332bfaa3a329e7976c0ee9538ede7d8232f81ac528862ae`, 9848 bytes)
  - P (1):
    - `materials/exploit/solve/exploit.py` ← `work/materials/pwn-v11/saj-2023-pwn-strings/solve/solve/exploit.py` (`cbdcb6b4dc2b7e89dbc7ab55d4adb341cf512cd3a084a0b9d6153696706cf21c`, 176 bytes)
  - B (5):
    - `materials/deployment/src/Dockerfile` ← `work/materials/pwn-v11/saj-2023-pwn-strings/build/src/Dockerfile` (`6aa9b42620c5cc61158bca1ffb1a5a9f98c0decf4832bf8bf03754fe02291693`, 782 bytes)
    - `materials/deployment/src/Makefile` ← `work/materials/pwn-v11/saj-2023-pwn-strings/build/src/Makefile` (`f9cb7571a2aa2deea6467582a155f9f1826ec3fccafc5c4a453b04e583c1d8b8`, 36 bytes)
    - `materials/deployment/src/chall.c` ← `work/materials/pwn-v11/saj-2023-pwn-strings/build/src/chall.c` (`9a9a0472fbb8285da2b55980b3d7bc776b856fe47e4f93db1f70f3e92cc04430`, 546 bytes)
    - `materials/deployment/src/docker-compose.yaml` ← `work/materials/pwn-v11/saj-2023-pwn-strings/build/src/docker-compose.yaml` (`0575a1774657182532313422b81e059915a30c877998a643628c520962699071`, 171 bytes)
    - `materials/deployment/src/xinetd` ← `work/materials/pwn-v11/saj-2023-pwn-strings/build/src/xinetd` (`ec24203d604227010ad7bf444a600209d3bb6e3f1476764a2ed8b950ccf4d742`, 588 bytes)

### 70. `gh-d7c4052e4b4f5e1bdfb491ff` — InTheWild

- Identity: breizhctf / 2024 / Pwn
- Source: `BreizhCTF/breizhctf-2024`; `https://github.com/BreizhCTF/breizhctf-2024/tree/a0464a7f243778664c8eb44cd5d700c2ed89f3ba/Pwn/InTheWild`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile_compose`; `source_build`; `unknown_or_non_elf`; `stack_rop`
- Selection reason: adds event breizhctf; adds source BreizhCTF/breizhctf-2024
- Material fingerprint: `c3b71f4eced933336d31bcf7f7bbc88bb429d128419e1c4cef146fd5f1158a94`
- Material paths:
  - A (3):
    - `materials/attachments/inthewild.jpeg` ← `work/materials/pwn-v11/gh-d7c4052e4b4f5e1bdfb491ff/public/inthewild.jpeg` (`241d90006d070d19b070b852b2ef09b66697f4cca386692e7d5769f325ce42ab`, 165782 bytes)
    - `materials/attachments/inthewild.pcap` ← `work/materials/pwn-v11/gh-d7c4052e4b4f5e1bdfb491ff/public/inthewild.pcap` (`a2a0f65ebdd412077d25bd22309d9fa3b20659173e9d00a586465d2757b69c4d`, 12186 bytes)
    - `materials/attachments/main.c` ← `work/materials/pwn-v11/gh-d7c4052e4b4f5e1bdfb491ff/public/main.c` (`f975eb8d64a092b6a6bbad9b0d0808f99c83e51f68b00f4533fdac7137997036`, 1871 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solve/solve.py` ← `work/materials/pwn-v11/gh-d7c4052e4b4f5e1bdfb491ff/solve/solve/solve.py` (`d039b1b9ff61961222b3e88f313e276d89ec930de4482ca8665b6a372cb749d8`, 2773 bytes)
  - B (4):
    - `materials/deployment/src/Dockerfile` ← `work/materials/pwn-v11/gh-d7c4052e4b4f5e1bdfb491ff/build/src/Dockerfile` (`ad4bf37015da58b67dfbbb20b83a05215ad043dabf2c836e0567bb1e64509a10`, 411 bytes)
    - `materials/deployment/src/Makefile` ← `work/materials/pwn-v11/gh-d7c4052e4b4f5e1bdfb491ff/build/src/Makefile` (`badb66789d34d9001916baed6dafd4f58522e2092c300fe3de24f286f84e683e`, 115 bytes)
    - `materials/deployment/src/docker-compose.yml` ← `work/materials/pwn-v11/gh-d7c4052e4b4f5e1bdfb491ff/build/src/docker-compose.yml` (`0ec3bce4ee16c35db7de84d26a4da54a469b30315b984aa5e4cd557a4335a68d`, 179 bytes)
    - `materials/deployment/src/main.c` ← `work/materials/pwn-v11/gh-d7c4052e4b4f5e1bdfb491ff/build/src/main.c` (`f975eb8d64a092b6a6bbad9b0d0808f99c83e51f68b00f4533fdac7137997036`, 1871 bytes)

### 71. `saj-2025-pwn-heap-of-the-brave` — Heap_Of_The_Brave

- Identity: Pragyan / 2025 / Pwn
- Source: `delta/PCTF25-Writeups`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/Pragyan/2025/pwn/Heap_Of_The_Brave`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `bundled_libc_loader`; `heap`
- Selection reason: adds event Pragyan; adds source delta/PCTF25-Writeups
- Material fingerprint: `e7ff37222fae2a16c5d23296d061ad8232e3d70316f3045c19770ea247fa4d49`
- Material paths:
  - A (4):
    - `materials/attachments/challenge/chal` ← `work/materials/pwn-v11/saj-2025-pwn-heap-of-the-brave/public/challenge/chal` (`41c471519d2e2bb97a451da729fe7adeaa14755af185d47bef57d422190c2b00`, 13384 bytes)
    - `materials/attachments/challenge/ld-linux-x86-64.so.2` ← `work/materials/pwn-v11/saj-2025-pwn-heap-of-the-brave/public/challenge/ld-linux-x86-64.so.2` (`bda7f01fd4270e84a0f56bb7f4432c5f35793f1bd688d52aa6ac0038506b0875`, 162632 bytes)
    - `materials/attachments/challenge/libc.so.6` ← `work/materials/pwn-v11/saj-2025-pwn-heap-of-the-brave/public/challenge/libc.so.6` (`926ee3653de7b71c8567061f3a4dfbc2ea91b6df2b49a05f11351fe1addf20cf`, 1868984 bytes)
    - `materials/attachments/docker_run.sh` ← `work/materials/pwn-v11/saj-2025-pwn-heap-of-the-brave/public/docker_run.sh` (`961f8a0e04d7ba389dace5d334e2cc574277a2e2899f59a22c1ca675026cbf4c`, 136 bytes)
  - W (1):
    - `materials/writeups/writeup.md` ← `work/materials/pwn-v11/saj-2025-pwn-heap-of-the-brave/writeups/writeup.md` (`498f2d55fd72dbe8b2ae805d8b689ed911bb9051d1fdbbb235a13381c2cbd7ba`, 3705 bytes)
  - P (1):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2025-pwn-heap-of-the-brave/solve/solve.py` (`dd250f7f50b28ac0291b960d550bb889cc890ca262da63936d28caa677a1f82a`, 1753 bytes)
  - B (5):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2025-pwn-heap-of-the-brave/build/Dockerfile` (`a72d6b306e02beb9613d85dfb3c548edd68f27b0e32145b7a240a8a90501a91a`, 412 bytes)
    - `materials/deployment/docker_run.sh` ← `work/materials/pwn-v11/saj-2025-pwn-heap-of-the-brave/build/docker_run.sh` (`961f8a0e04d7ba389dace5d334e2cc574277a2e2899f59a22c1ca675026cbf4c`, 136 bytes)
    - `materials/deployment/includes/Dockerfile` ← `work/materials/pwn-v11/saj-2025-pwn-heap-of-the-brave/build/includes/Dockerfile` (`898c84ad91cb9c938386e44a463513fed1e9a286997d4d55383a6b232c1e6789`, 220 bytes)
    - `materials/deployment/includes/compose.yml` ← `work/materials/pwn-v11/saj-2025-pwn-heap-of-the-brave/build/includes/compose.yml` (`e6db9efe1f2d6624b962faf6ba4b6e527ca5fa266c2847aadd6d78c0f4e2d8bb`, 208 bytes)
    - `materials/deployment/source.c` ← `work/materials/pwn-v11/saj-2025-pwn-heap-of-the-brave/build/source.c` (`a149847f0ccc74943dd15b8c5d787f1ca4107e67aebdc5a351346cdef2c1e1ec`, 3930 bytes)

### 72. `saj-2024-pwn-where2go` — where2go

- Identity: SwampCTF / 2024 / Pwn
- Source: `ufsit/SwampCTF-2025-Challenges`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/SwampCTF/2024/pwn/where2go`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `build_metadata`; `hybrid`; `system_libc`; `stack_rop`
- Selection reason: adds event SwampCTF; adds source ufsit/SwampCTF-2025-Challenges
- Material fingerprint: `785825a2428969b6ba7ff77cee15729d5ca2a8e6bf0899a597b8fc15ed6dc960`
- Material paths:
  - A (2):
    - `materials/attachments/gadgets.txt` ← `work/materials/pwn-v11/saj-2024-pwn-where2go/public/gadgets.txt` (`0170e13a71b455034127abaf0b7a0fb6f65ec3c13c5052a60a7be68eaa840c25`, 7042 bytes)
    - `materials/attachments/where2go` ← `work/materials/pwn-v11/saj-2024-pwn-where2go/public/where2go` (`0f634d50519b03508fde6cb75830bcb81fe69cb259aed47acae02cc2188f4800`, 7112 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2024-pwn-where2go/solve/solve.py` (`296ed62da2586b0893b52099b4805dcd9c3600541124b98547bab7fc50638298`, 1312 bytes)
  - B (1):
    - `materials/deployment/Makefile` ← `work/materials/pwn-v11/saj-2024-pwn-where2go/build/Makefile` (`1a195076b06bc4c489e5e4af08f43868890b35934256a84bd677664d980b8479`, 149 bytes)

### 73. `gh-ecda0c754e536cafb96812b6` — wine

- Identity: pico ctf / 2022 / Pwn
- Source: `CavemanJay/PicoCTF`; `https://github.com/CavemanJay/PicoCTF/tree/40f2d5eba4f9aabd5975e46e8aee436b887d61af/2022/binary_exploitation/wine`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `build_metadata`; `source_build`; `unknown_or_non_elf`; `shellcode_seccomp`
- Selection reason: adds event pico ctf; adds source CavemanJay/PicoCTF
- Material fingerprint: `1379e55da2b0139010abf9bda58a6a378f695516822f0c1db4f315e1b52f3da4`
- Material paths:
  - A (18):
    - `materials/attachments/FUFaR7BXoAIvrcS.jpg` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/public/FUFaR7BXoAIvrcS.jpg` (`a4c18077f4c28da9fc5b19ba4a583afcbb9834e19d34014c90c2e0e68f71f653`, 52457 bytes)
    - `materials/attachments/FUFaSQqWQAET18G.jpg` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/public/FUFaSQqWQAET18G.jpg` (`21a8a54d338025beeb6987d43789e542124ed3afd8c3adaf0e8f899836609f17`, 78490 bytes)
    - `materials/attachments/What I tried.txt` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/public/What I tried.txt` (`9270075f93450f3303a2d5762ca194d03ada085f16326bf8fa5d9f13b3e8d9c2`, 687 bytes)
    - `materials/attachments/pwn_cyclic_offset.png` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/public/pwn_cyclic_offset.png` (`3a767bbd65224b922c802703847bb627ddf377f120d0c6cb0f56695c9b0a854b`, 27913 bytes)
    - `materials/attachments/readme.txt` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/public/readme.txt` (`c0031d5064fb2da8f247f55f8f6895b743beaccb766b494dc70cb1043be0a5b3`, 1664 bytes)
    - `materials/attachments/vuln-modified.c` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/public/vuln-modified.c` (`7108d15e05e2a112da42d2557b192f289822b2301382dd00a4629c830560e711`, 747 bytes)
    - `materials/attachments/vuln.520abe80.c` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/public/vuln.520abe80.c` (`afb2ab8b149370a5118ba4a2f122ae7774eea82bf7744d3ce62bb527b9a66e36`, 599 bytes)
    - `materials/attachments/vuln.7f6f5690.exe` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/public/vuln.7f6f5690.exe` (`877811459755814d4bc414dc5fb413de81d2be81a0945b4ba4c46c400f54bea9`, 288832 bytes)
    - `materials/attachments/vuln.aae94cf6.exe` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/public/vuln.aae94cf6.exe` (`232795f11d18fe36b4393475fba6157bb552d06cd8e5099cf5a5e88a10b0cdba`, 288832 bytes)
    - `materials/attachments/vuln.c` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/public/vuln.c` (`c3a01e8a42265b07f6d2cd1c998742efa81c1766dcc5881fb403d4250bf08659`, 662 bytes)
    - `materials/attachments/vuln.d6a96c30.c` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/public/vuln.d6a96c30.c` (`d6e140ec4feae84233a3b6ffdadc27040d794c383bc2050d5b4f4db7b1b958ea`, 667 bytes)
    - `materials/attachments/vuln.exe` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/public/vuln.exe` (`25254763a38b7d7dfc132d7095fcd43a8cea8790406cb1585ffb8e39c9672e72`, 288832 bytes)
    - `materials/attachments/vuln.exe.dump` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/public/vuln.exe.dump` (`dfab22647f18d184424f1d56e200ddd1f8b788221ceafb82d6774ea0aaf2a199`, 7189053 bytes)
    - `materials/attachments/vuln_modified.exe` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/public/vuln_modified.exe` (`efa933a2a82b2f7a4f002243064b4b0f592937d05f1fb7e188965a3dbfd739f3`, 289008 bytes)
    - `materials/attachments/vuln_source_modified.png` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/public/vuln_source_modified.png` (`82f303066da0a3e1c2cc6f271e0a30dd27bd690686fb5e771c3cd11d143f63e7`, 18335 bytes)
    - `materials/attachments/win_address.png` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/public/win_address.png` (`53e0c799235ae9ca784406e2617fe35c53e5340af7c0f67481c908ff151f4892`, 6848 bytes)
    - `materials/attachments/wine.txt` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/public/wine.txt` (`3f87a82ce1a2cb5f3b7e35a01de426f3956cc7572ae574f9181c20db55fe4460`, 535 bytes)
    - `materials/attachments/wine_segfault.png` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/public/wine_segfault.png` (`d27378d078d34552be8531108939b19ba27322458d60cb3a48fd470139dd2242`, 57011 bytes)
  - W (3):
    - `materials/writeups/README.ad1d25be.md` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/writeups/README.ad1d25be.md` (`a29299afaecfea8fd25238261131d810789d6bacc3c86d6537c62062484e9347`, 3581 bytes)
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/writeups/README.md` (`22cab8371bfa748d39eeb737a67525cf209bf6925c7bf6ad6c43f827241a0666`, 3323 bytes)
    - `materials/writeups/Readme.md` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/writeups/Readme.md` (`07ae43875b8bfe5722bea598b7c85b2441ae90e30efcb4c25048bca2e7c2c13c`, 245 bytes)
  - P (2):
    - `materials/exploit/Wine_exploit.py` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/solve/Wine_exploit.py` (`00f99db18ae9d495082a5e75e996f73d169275b647c77386dcf0c3d9f2dcafa9`, 1794 bytes)
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/solve/solve.py` (`6246186a42cb83e42ab85a565088fbeedc96f949e4c2452a1b6d33ccbff25a53`, 237 bytes)
  - B (1):
    - `materials/deployment/Makefile` ← `work/materials/pwn-v11/gh-ecda0c754e536cafb96812b6/build/Makefile` (`dfa83f8d89f1a210c8b9fea16d4d20c945d06db0ed378fda40a730686977bb77`, 175 bytes)

### 74. `saj-2025-pwn-heapie-2` — Heapie_2

- Identity: CrateCTF / 2025 / Pwn
- Source: `CrateOrg/crate-ctf`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/CrateCTF/2025/pwn/Heapie_2`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `static`; `heap`
- Selection reason: adds event CrateCTF; adds source CrateOrg/crate-ctf
- Material fingerprint: `3259222a570b8ef199ce916986abc76170a5e0071856c79b12465400f3d860e7`
- Material paths:
  - A (5):
    - `materials/attachments/README.md` ← `work/materials/pwn-v11/saj-2025-pwn-heapie-2/public/README.md` (`5e3a2ab65ebafbd680e0e1485aaee1ef2fe68ed720de92c8a8af07ad161a6dc3`, 46 bytes)
    - `materials/attachments/challenge.yml` ← `work/materials/pwn-v11/saj-2025-pwn-heapie-2/public/challenge.yml` (`42125375e510743ce35c47faa2a09b916ff9275fe04b95f4ef7d3ebf7c080438`, 417 bytes)
    - `materials/attachments/heapie2` ← `work/materials/pwn-v11/saj-2025-pwn-heapie-2/public/heapie2` (`19dea9390b956f3b4080001090579ae5dd230cdd314f1ec75308dfcb90845ded`, 766085 bytes)
    - `materials/attachments/heapie2.zig` ← `work/materials/pwn-v11/saj-2025-pwn-heapie-2/public/heapie2.zig` (`2fb913a1a84b25673a235e9215c543a021d3d82433ed9651a8bfb8d7fcb65509`, 3628 bytes)
    - `materials/attachments/setaff.c` ← `work/materials/pwn-v11/saj-2025-pwn-heapie-2/public/setaff.c` (`b72184c0833556372d8f322ff8be31b0737b1db9f2950a000e05ecd0636828e6`, 374 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2025-pwn-heapie-2/solve/solve.py` (`e58ccc8301437af52088e7357523cc2794f94d960ae1e8e0a22b126975630ed5`, 7910 bytes)
  - B (3):
    - `materials/deployment/docker/Dockerfile` ← `work/materials/pwn-v11/saj-2025-pwn-heapie-2/build/docker/Dockerfile` (`d3da4e96f6feae6ebbf207ebb41f1af7d445acc57faead7a60fdf998166feee8`, 185 bytes)
    - `materials/deployment/docker/compose.yaml` ← `work/materials/pwn-v11/saj-2025-pwn-heapie-2/build/docker/compose.yaml` (`9c7e7e96f4373feefe83c535a2511b832a2c62e340e0ddd9173bd41d1fdaa7cf`, 178 bytes)
    - `materials/deployment/setaff.c` ← `work/materials/pwn-v11/saj-2025-pwn-heapie-2/build/setaff.c` (`b72184c0833556372d8f322ff8be31b0737b1db9f2950a000e05ecd0636828e6`, 374 bytes)

### 75. `gh-cbaaa754ed2e2122d2b51b00` — stop-rop-n-roll

- Identity: redpwnctf / 2019 / Pwn
- Source: `redpwn/redpwnctf-2019-challenges`; `https://github.com/redpwn/redpwnctf-2019-challenges/tree/68fe2c30acf697c9ca246cd209398a5c14969ce9/pwn/stop-rop-n-roll`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `system_libc`; `shellcode_seccomp`, `stack_rop`
- Selection reason: adds event redpwnctf; adds source redpwn/redpwnctf-2019-challenges
- Material fingerprint: `a29c90258b5cf61773bc77157b2fa8e9db319e7f653fa330e54be0b10bb30622`
- Material paths:
  - A (3):
    - `materials/attachments/srnr` ← `work/materials/pwn-v11/gh-cbaaa754ed2e2122d2b51b00/public/srnr` (`b74ec42a971db3b206defeac363778ce1d1f7d4521b0c700ed43f841aac4323a`, 12744 bytes)
    - `materials/attachments/srnr.c` ← `work/materials/pwn-v11/gh-cbaaa754ed2e2122d2b51b00/public/srnr.c` (`c0da9e5045810bb28c4af7ee945c2e087e94c311d221273899426a0da2a10b80`, 1847 bytes)
    - `materials/attachments/srnr.py` ← `work/materials/pwn-v11/gh-cbaaa754ed2e2122d2b51b00/public/srnr.py` (`1f67a2256a9de802883153f88086aab7aa782909880b4861a19f8b0121ac2d09`, 518 bytes)
  - W (2):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/gh-cbaaa754ed2e2122d2b51b00/writeups/README.md` (`dadbcf350eed8787d26c2145a86ed8519b0840a86a7dcdebcddc3e3a3faf0cbd`, 1846 bytes)
    - `materials/writeups/RedpwnCTF_2019.md` ← `work/materials/pwn-v11/gh-cbaaa754ed2e2122d2b51b00/writeups/RedpwnCTF_2019.md` (`5b32d3d074791bbb43214ddf2a85c544a43d1f44a44d44d99596cdeb80725774`, 6212 bytes)
  - P (2):
    - `materials/exploit/solve.98387b14.py` ← `work/materials/pwn-v11/gh-cbaaa754ed2e2122d2b51b00/solve/solve.98387b14.py` (`2186853b39d5abfcfee79b478028c9844cae2cc2101eeb337c8b422c29ec9c5b`, 951 bytes)
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/gh-cbaaa754ed2e2122d2b51b00/solve/solve.py` (`c01232849289e36d434762bf4f8f99169178dcd8c46452fdd4fbcedf86a77d7a`, 704 bytes)
  - B (4):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-cbaaa754ed2e2122d2b51b00/build/Dockerfile` (`249f8d9ddb1e12f7287e1a61abcb5758094e32d9409e93c1a0099de5c05f26e9`, 969 bytes)
    - `materials/deployment/bin/Makefile` ← `work/materials/pwn-v11/gh-cbaaa754ed2e2122d2b51b00/build/bin/Makefile` (`2c78ee01accc006148aeae6ed2ed0f044e8dcae129411d99fc24e01f9d3b16b3`, 118 bytes)
    - `materials/deployment/bin/srnr.c` ← `work/materials/pwn-v11/gh-cbaaa754ed2e2122d2b51b00/build/bin/srnr.c` (`c0da9e5045810bb28c4af7ee945c2e087e94c311d221273899426a0da2a10b80`, 1847 bytes)
    - `materials/deployment/start.sh` ← `work/materials/pwn-v11/gh-cbaaa754ed2e2122d2b51b00/build/start.sh` (`3197e89b05525ebb9d76bad1d14cf124f88ec8647fd475a013b757ab6614a46d`, 96 bytes)

### 76. `gh-a98554e0613cbd503e87d10b` — pwn-beginners-rop

- Identity: WaniCTF / 2023 / Pwn
- Source: `min-yang/CTF-Challenge-Collection`; `https://github.com/min-yang/CTF-Challenge-Collection/tree/fe50cc8e7bfbbb77c94f46ec8aaedd9c33a10887/WaniCTF2023/Pwn/pwn-beginners-rop`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `build_metadata`; `source_build`; `unknown_or_non_elf`; `other`
- Selection reason: adds event WaniCTF; adds source min-yang/CTF-Challenge-Collection
- Material fingerprint: `f04604ddbd992f46c2504592754f78f7c072bcd6f516e9f166834d16f2de8ec4`
- Material paths:
  - A (1):
    - `materials/attachments/main.c` ← `work/materials/pwn-v11/gh-a98554e0613cbd503e87d10b/public/main.c` (`b97be054ac89f55d27cb1f1811970210582eb5dac175db49fd1fe2869c94d387`, 1636 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/gh-a98554e0613cbd503e87d10b/solve/solve.py` (`5fcc53048839ec44161440eb947a692b122feac08f48cdd83000d1e23ed40ae6`, 595 bytes)
  - B (1):
    - `materials/deployment/Makefile` ← `work/materials/pwn-v11/gh-a98554e0613cbd503e87d10b/build/Makefile` (`e80b972db689ebb9df5210c884b20b7889563a2437184a38803541c830fa7834`, 166 bytes)

### 77. `gh-e01f4b11a572699f3695620b` — devpro

- Identity: Blackhat MEA CTF / 2023 / Pwn
- Source: `nobodyisnobody/write-ups`; `https://github.com/nobodyisnobody/write-ups/tree/b9cec85168dd73a9e9329b44420024c64f48b8c1/Blackhat.MEA.CTF.Finals.2023/pwn/devpro`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `bundled_libc_loader`; `other`
- Selection reason: adds event Blackhat MEA CTF; adds source nobodyisnobody/write-ups
- Material fingerprint: `ba1ecce61087470cc3ed443587c086eb2448e0ab2a2b028d707a8728eee25aca`
- Material paths:
  - A (7):
    - `materials/attachments/devpro` ← `work/materials/pwn-v11/gh-e01f4b11a572699f3695620b/public/devpro` (`a319df2a9f1c13a11593b01010f96d749eb11a6b8d2d034eafe224ff74a90899`, 16992 bytes)
    - `materials/attachments/devpro_patched` ← `work/materials/pwn-v11/gh-e01f4b11a572699f3695620b/public/devpro_patched` (`98bb8f2fb126edd4b719417bb19eec5567d15de2af3278c349497924c87bc42e`, 25377 bytes)
    - `materials/attachments/file1.png` ← `work/materials/pwn-v11/gh-e01f4b11a572699f3695620b/public/file1.png` (`e306fab2773133ba48a1615ccb88e07a4c87a2938c77c520b8da3a105fd38381`, 153111 bytes)
    - `materials/attachments/heap1.png` ← `work/materials/pwn-v11/gh-e01f4b11a572699f3695620b/public/heap1.png` (`3d43e2c4990adbec2f69b51d45657ae4dfa7e2db470fda315b119516ce83f9e8`, 31589 bytes)
    - `materials/attachments/ld-2.35.so` ← `work/materials/pwn-v11/gh-e01f4b11a572699f3695620b/public/ld-2.35.so` (`ee7aa16bd8443a946286c9ab84a0af0cbc47aa53a8f00477bf8ada5c38580a36`, 240936 bytes)
    - `materials/attachments/libc.so.6` ← `work/materials/pwn-v11/gh-e01f4b11a572699f3695620b/public/libc.so.6` (`fdaa44be131da64b35f6b132cbb612e0acdd49ca0d29fd247d023619835231e4`, 6616616 bytes)
    - `materials/attachments/main.c` ← `work/materials/pwn-v11/gh-e01f4b11a572699f3695620b/public/main.c` (`7ee6762e6022d59490864c465bd1c353ed5459038cf52d3e207767600c06049d`, 2308 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/gh-e01f4b11a572699f3695620b/writeups/README.md` (`7fb203fb16cdbeea9302e9d048e4480603bb57ab13d9d84eec59278f13efca35`, 14498 bytes)
  - P (1):
    - `materials/exploit/working.exploit.py` ← `work/materials/pwn-v11/gh-e01f4b11a572699f3695620b/solve/working.exploit.py` (`ced11c4dc9597b22e13431797029aa6918ecfde21b4e7e1706cc4680fd7cf52a`, 3518 bytes)
  - B (5):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-e01f4b11a572699f3695620b/build/Dockerfile` (`d7a81fc45c17d1df2fa0a314264d4cee7a1d2eb27222919980f9787b0934be4c`, 347 bytes)
    - `materials/deployment/Dockerfile.1848df17` ← `work/materials/pwn-v11/gh-e01f4b11a572699f3695620b/build/Dockerfile.1848df17` (`2ef3308f238e3e3f0fc82b50925119c48e8d27711518f167d57e2f28db32ca57`, 345 bytes)
    - `materials/deployment/docker-compose.9e5a5c8a.yml` ← `work/materials/pwn-v11/gh-e01f4b11a572699f3695620b/build/docker-compose.9e5a5c8a.yml` (`ccd6a36eed71a34b4fa90995d326669f3b24854373d3f0569092a11104496e45`, 131 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/gh-e01f4b11a572699f3695620b/build/docker-compose.yml` (`dc68580f159966fc07b1d3357a3011848b2bfec5e2edc9afdb4136245840caba`, 163 bytes)
    - `materials/deployment/main.c` ← `work/materials/pwn-v11/gh-e01f4b11a572699f3695620b/build/main.c` (`7ee6762e6022d59490864c465bd1c353ed5459038cf52d3e207767600c06049d`, 2308 bytes)

### 78. `gh-6cb1ca15dc12bb57d1e8f954` — gonta-ganti

- Identity: hcs intersec ctf / 2023 / Pwn
- Source: `Heroes-Cyber-Security/2023-hcs-intersec-ctf`; `https://github.com/Heroes-Cyber-Security/2023-hcs-intersec-ctf/tree/4c23bc6bc5639f9ed256db6f76e84176640cf495/pwn/gonta-ganti`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `system_libc`; `other`
- Selection reason: adds event hcs intersec ctf; adds source Heroes-Cyber-Security/2023-hcs-intersec-ctf
- Material fingerprint: `261c4fc772a2bef5a5704dfa40941565369bf884cf9bbd47d6f05aadd5f8a260`
- Material paths:
  - A (3):
    - `materials/attachments/chall` ← `work/materials/pwn-v11/gh-6cb1ca15dc12bb57d1e8f954/public/chall` (`16b70b696bdcc2474638a3284cb9dc10bc5e5d82d4e008bf495b12085a4bf930`, 16472 bytes)
    - `materials/attachments/gonta-ganti.c` ← `work/materials/pwn-v11/gh-6cb1ca15dc12bb57d1e8f954/public/gonta-ganti.c` (`85e90904f5ddeeb63a58ac88b76d2e28cb4a8875d5ef70c1d14e06962b9c5b78`, 648 bytes)
    - `materials/attachments/gonta-ganti.fb1d0fbf.c` ← `work/materials/pwn-v11/gh-6cb1ca15dc12bb57d1e8f954/public/gonta-ganti.fb1d0fbf.c` (`5ccbee47212aee5b2b0548498cabf21055763cf897a3147baabc154b0b4de589`, 1271 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solve/solve.py` ← `work/materials/pwn-v11/gh-6cb1ca15dc12bb57d1e8f954/solve/solve/solve.py` (`9b0c09f24b9cf5afe1d79631331f90a8a2a948b0d23028f5a498e10341fea804`, 314 bytes)
  - B (4):
    - `materials/deployment/dist/gonta-ganti.c` ← `work/materials/pwn-v11/gh-6cb1ca15dc12bb57d1e8f954/build/dist/gonta-ganti.c` (`85e90904f5ddeeb63a58ac88b76d2e28cb4a8875d5ef70c1d14e06962b9c5b78`, 648 bytes)
    - `materials/deployment/src/Dockerfile` ← `work/materials/pwn-v11/gh-6cb1ca15dc12bb57d1e8f954/build/src/Dockerfile` (`3400d45759d375012e5e7c27ea915b6b80d4fa6e4cc3c748f1d99f6b70a3390b`, 399 bytes)
    - `materials/deployment/src/Makefile` ← `work/materials/pwn-v11/gh-6cb1ca15dc12bb57d1e8f954/build/src/Makefile` (`2c9c69074d6bc7f6f84798b330515c08de14bffeb4a428550adcc520d4d4940f`, 159 bytes)
    - `materials/deployment/src/gonta-ganti.c` ← `work/materials/pwn-v11/gh-6cb1ca15dc12bb57d1e8f954/build/src/gonta-ganti.c` (`5ccbee47212aee5b2b0548498cabf21055763cf897a3147baabc154b0b4de589`, 1271 bytes)

### 79. `gh-35cbfd8fcff12adf3fa3717a` — cant-find-me

- Identity: kid20 / 2020 / Pwn
- Source: `ItemizeNTNU/kid20-challenges`; `https://github.com/ItemizeNTNU/kid20-challenges/tree/67c99a545cf34137379082bf9ff490b85d9fdf58/pwn/cant-find-me`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `system_libc`; `other`
- Selection reason: adds event kid20; adds source ItemizeNTNU/kid20-challenges
- Material fingerprint: `40ef4c8cdc3f27a3141852981ebe58a8f089259fdbeb05334b837bce9e7fca59`
- Material paths:
  - A (5):
    - `materials/attachments/cant-find-me` ← `work/materials/pwn-v11/gh-35cbfd8fcff12adf3fa3717a/public/cant-find-me` (`15684cca787deb980689093c7525f52d6fb69dbf5b93103ad44f4a0e3969ebf3`, 17320 bytes)
    - `materials/attachments/cant-find-me.1d3b50f3.c` ← `work/materials/pwn-v11/gh-35cbfd8fcff12adf3fa3717a/public/cant-find-me.1d3b50f3.c` (`d43edd136ed6c117da271c19ecd599a05c054321fd70f152bc89301c03047b47`, 748 bytes)
    - `materials/attachments/cant-find-me.35032be2` ← `work/materials/pwn-v11/gh-35cbfd8fcff12adf3fa3717a/public/cant-find-me.35032be2` (`f665b705ee287a5b05aeab66bb3f52502b7415d3ed5fae56a06b1161a0da1e2a`, 17336 bytes)
    - `materials/attachments/cant-find-me.c` ← `work/materials/pwn-v11/gh-35cbfd8fcff12adf3fa3717a/public/cant-find-me.c` (`3535730b5ad087f49c5e883f79d4f1a9949da1c50771f35f776115c57c10d0d5`, 732 bytes)
    - `materials/attachments/ynetd` ← `work/materials/pwn-v11/gh-35cbfd8fcff12adf3fa3717a/public/ynetd` (`481a6381e16a7e177c54533537cb63a3b48e500f6f39dea7cc9dd3e42cdb22cb`, 18744 bytes)
  - W (1):
    - `materials/writeups/writeup.md` ← `work/materials/pwn-v11/gh-35cbfd8fcff12adf3fa3717a/writeups/writeup.md` (`ade05b3385ad80eed368da0e1b9f2efd394924a9c8f74b5fe424b76fa44a8015`, 1925 bytes)
  - P (3):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/gh-35cbfd8fcff12adf3fa3717a/solve/solve.py` (`3ebc277d1b4b228e57f7b2b0e554361ad7e40b95ee430aceb0bb2b462c1545ef`, 114 bytes)
    - `materials/exploit/writeup/solve.png` ← `work/materials/pwn-v11/gh-35cbfd8fcff12adf3fa3717a/solve/writeup/solve.png` (`f24ddb1742dba7dc314c4787c850bd7fd2f69560a54a4550612631d66931fb67`, 169881 bytes)
    - `materials/exploit/writeup/solve.py` ← `work/materials/pwn-v11/gh-35cbfd8fcff12adf3fa3717a/solve/writeup/solve.py` (`436ab91f0257f11d5b810e410e8f953d78389df673d0be7bc2c950f8bf502838`, 233 bytes)
  - B (5):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-35cbfd8fcff12adf3fa3717a/build/Dockerfile` (`09986357e4e4618d75550c9a0e5673b07fa822359aad539d5058a0b130d6a32f`, 334 bytes)
    - `materials/deployment/Makefile` ← `work/materials/pwn-v11/gh-35cbfd8fcff12adf3fa3717a/build/Makefile` (`8f586aeb1ed76fa0fc6b7a7a1e76e0329b95e1706ffc70b2f929c2c39c5ef7c5`, 75 bytes)
    - `materials/deployment/cant-find-me.c` ← `work/materials/pwn-v11/gh-35cbfd8fcff12adf3fa3717a/build/cant-find-me.c` (`d43edd136ed6c117da271c19ecd599a05c054321fd70f152bc89301c03047b47`, 748 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/gh-35cbfd8fcff12adf3fa3717a/build/docker-compose.yml` (`413ea73fd4103020d7e173fab528efbdb19025841b4d5857026c06c9f7fe947f`, 101 bytes)
    - `materials/deployment/files/cant-find-me.c` ← `work/materials/pwn-v11/gh-35cbfd8fcff12adf3fa3717a/build/files/cant-find-me.c` (`3535730b5ad087f49c5e883f79d4f1a9949da1c50771f35f776115c57c10d0d5`, 732 bytes)

### 80. `gh-617f8961bbd57146ec3859e1` — attempt

- Identity: MetaCTF / 2021 / Pwn
- Source: `kyfuse/ctf-archive`; `https://github.com/kyfuse/ctf-archive/tree/5063cd2889cd300aade440429faf9c4ca68511ef/MetaCTF 2021/Binary/attempt`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `source_build`; `bundled_libc_only`; `stack_rop`
- Selection reason: adds event MetaCTF; adds source kyfuse/ctf-archive
- Material fingerprint: `35b60c8232457d57ca38b606309c7754bd3700eacab61701d08beda7c9f85d87`
- Material paths:
  - A (11):
    - `materials/attachments/chall.sh` ← `work/materials/pwn-v11/gh-617f8961bbd57146ec3859e1/public/chall.sh` (`9dfd58436a5a0ce8750e10150775cfd6f440f7387cd151e95fe671d711e5e81a`, 34 bytes)
    - `materials/attachments/gadgetschall.txt` ← `work/materials/pwn-v11/gh-617f8961bbd57146ec3859e1/public/gadgetschall.txt` (`b743353aecbf86acdbc2b85e271c6a32fd73eb68770a104ccc0dc059416f81f1`, 5681 bytes)
    - `materials/attachments/gadgetslibc.txt` ← `work/materials/pwn-v11/gh-617f8961bbd57146ec3859e1/public/gadgetslibc.txt` (`01197277515f5616266cc1570d38f7090f9e376302aececdb66d49bfa9fe8aff`, 6634283 bytes)
    - `materials/attachments/init.sh` ← `work/materials/pwn-v11/gh-617f8961bbd57146ec3859e1/public/init.sh` (`e00b2bb9b5cc431b908b8b5a4298a3bd3984ee2fac85a7e7f4e9cab3d402ff83`, 59 bytes)
    - `materials/attachments/ld.so` ← `work/materials/pwn-v11/gh-617f8961bbd57146ec3859e1/public/ld.so` (`507318e52fc4613c67d0b564f8a4be959e5b2ea72621c5bc6c76619eef7eff5b`, 229568 bytes)
    - `materials/attachments/libc.so.6` ← `work/materials/pwn-v11/gh-617f8961bbd57146ec3859e1/public/libc.so.6` (`cec05a3628872b27c16a2000b4d6985447a0d6426c19038132333ea5c5615d4a`, 13882792 bytes)
    - `materials/attachments/rop.txt` ← `work/materials/pwn-v11/gh-617f8961bbd57146ec3859e1/public/rop.txt` (`d55a4bd178f73526a8f7ef0093fdef19054afbe68648f9f77a5daaab9132416a`, 4945356 bytes)
    - `materials/attachments/ropper1.txt` ← `work/materials/pwn-v11/gh-617f8961bbd57146ec3859e1/public/ropper1.txt` (`1e6828a05b39746115a4defed29b17698d83050ce6e5444826dbe2cc21952d57`, 15974869 bytes)
    - `materials/attachments/ropper2.txt` ← `work/materials/pwn-v11/gh-617f8961bbd57146ec3859e1/public/ropper2.txt` (`d7fddeb533bd7fe1a5c9a6b81e835a6fa62b95bdb851a667aa4542d321d722ed`, 29139 bytes)
    - `materials/attachments/test.cpp` ← `work/materials/pwn-v11/gh-617f8961bbd57146ec3859e1/public/test.cpp` (`ec70254a257ff0560d981c145b6d03093f62b40a4ec591c68daab5d355c78a72`, 331 bytes)
    - `materials/attachments/useful.txt` ← `work/materials/pwn-v11/gh-617f8961bbd57146ec3859e1/public/useful.txt` (`487074f8eab09e251a16123d760097a434e6daebf93a69e16fad70e12730e657`, 373 bytes)
  - W: absent
  - P (2):
    - `materials/exploit/exp` ← `work/materials/pwn-v11/gh-617f8961bbd57146ec3859e1/solve/exp` (`04fa713e8387629f6b1dfaa6346d691d9e17ae68c87be37b3bd965d03be6f402`, 244 bytes)
    - `materials/exploit/exploit.py` ← `work/materials/pwn-v11/gh-617f8961bbd57146ec3859e1/solve/exploit.py` (`0e439c4731e6a346252f2a138a79c11605066b3a9fd806607a6b83058ee168fe`, 5093 bytes)
  - B (4):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-617f8961bbd57146ec3859e1/build/Dockerfile` (`62f5192d4da1ac991c3b223be45aa1d193cedfbc1ac25c3e36b8742b9fc03b76`, 601 bytes)
    - `materials/deployment/chall.sh` ← `work/materials/pwn-v11/gh-617f8961bbd57146ec3859e1/build/chall.sh` (`9dfd58436a5a0ce8750e10150775cfd6f440f7387cd151e95fe671d711e5e81a`, 34 bytes)
    - `materials/deployment/init.sh` ← `work/materials/pwn-v11/gh-617f8961bbd57146ec3859e1/build/init.sh` (`e00b2bb9b5cc431b908b8b5a4298a3bd3984ee2fac85a7e7f4e9cab3d402ff83`, 59 bytes)
    - `materials/deployment/test.cpp` ← `work/materials/pwn-v11/gh-617f8961bbd57146ec3859e1/build/test.cpp` (`ec70254a257ff0560d981c145b6d03093f62b40a4ec591c68daab5d355c78a72`, 331 bytes)

### 81. `gh-678b0776161cb8ba38b0ddfe` — Tic-tac-toe

- Identity: CTFZone / 2019 / Pwn
- Source: `LJP-TW/CTF`; `https://github.com/LJP-TW/CTF/tree/f9c30cf270130120bfe4ddf957299fb60ddf8c27/CTFZone-2019/pwn/Tic-tac-toe`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `build_metadata`; `hybrid`; `system_libc`; `shellcode_seccomp`, `stack_rop`
- Selection reason: adds event CTFZone; adds source LJP-TW/CTF
- Material fingerprint: `28ae9085852fb603ade43be2baebfe12f99aeb63b0419fbb21d63459b0c4f72f`
- Material paths:
  - A (7):
    - `materials/attachments/Screenshot from 2019-12-01 09-00-51.png` ← `work/materials/pwn-v11/gh-678b0776161cb8ba38b0ddfe/public/Screenshot from 2019-12-01 09-00-51.png` (`c2b70cea8eeae5d9fabdd7a895c09fa77cc18c49a67d08c73b3cdd7ef5e24878`, 293059 bytes)
    - `materials/attachments/Screenshot from 2019-12-01 09-06-54.png` ← `work/materials/pwn-v11/gh-678b0776161cb8ba38b0ddfe/public/Screenshot from 2019-12-01 09-06-54.png` (`38a1190821c194f632b911369f7b4e638a79a6b762234121542901da20989d66`, 2296320 bytes)
    - `materials/attachments/server.939f3c17.py` ← `work/materials/pwn-v11/gh-678b0776161cb8ba38b0ddfe/public/server.939f3c17.py` (`81e2f84f41a75d964865e4c33ef51a37e1ebbaf041a338238a09339538f5528e`, 6811 bytes)
    - `materials/attachments/server.973e72ae.py` ← `work/materials/pwn-v11/gh-678b0776161cb8ba38b0ddfe/public/server.973e72ae.py` (`974344cbc9839990846f26e54232e734bec9df74a69e1eea1c7a802aac5a15d8`, 6754 bytes)
    - `materials/attachments/server.py` ← `work/materials/pwn-v11/gh-678b0776161cb8ba38b0ddfe/public/server.py` (`432dedb8311b777191d15a21c3652c79af46f196dce924c939b7d15ba1161886`, 6759 bytes)
    - `materials/attachments/shell.py` ← `work/materials/pwn-v11/gh-678b0776161cb8ba38b0ddfe/public/shell.py` (`68f6916bd761bbd3f63adccdfa5be376d0e4564fe249bcc1613a55093adabf7b`, 3791 bytes)
    - `materials/attachments/tictactoe` ← `work/materials/pwn-v11/gh-678b0776161cb8ba38b0ddfe/public/tictactoe` (`0278d963794ccf4e5b0f9b8fd7d3a4a41ac4d03f731b9a56bb8564b3b07acff2`, 43048 bytes)
  - W (4):
    - `materials/writeups/README.be319415.md` ← `work/materials/pwn-v11/gh-678b0776161cb8ba38b0ddfe/writeups/README.be319415.md` (`d7c7ff23a986b263742a1cbc881e86c7540d6b3b5943149bdda10aeb5d77d529`, 1157 bytes)
    - `materials/writeups/README.e1742871.md` ← `work/materials/pwn-v11/gh-678b0776161cb8ba38b0ddfe/writeups/README.e1742871.md` (`f5283d1b95b506991ca4635fead673df1f7d96ae5424ea0d8198aa396161f335`, 2212 bytes)
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/gh-678b0776161cb8ba38b0ddfe/writeups/README.md` (`dceab22682f08ec53f6544c05cdb45ff8b5a1ebd166d0c63722f626c8f2093e2`, 155 bytes)
    - `materials/writeups/WRITEUP.md` ← `work/materials/pwn-v11/gh-678b0776161cb8ba38b0ddfe/writeups/WRITEUP.md` (`3bf00c1e67d95f5e03f5bafacc781293554bb2df628ee9b6786355213a563281`, 7930 bytes)
  - P (4):
    - `materials/exploit/exp.py` ← `work/materials/pwn-v11/gh-678b0776161cb8ba38b0ddfe/solve/exp.py` (`322303bb546f0b28a05d050d00a24c0413cc912d5c39e6fb59e0e4f3a0afd80c`, 2295 bytes)
    - `materials/exploit/exploit.py` ← `work/materials/pwn-v11/gh-678b0776161cb8ba38b0ddfe/solve/exploit.py` (`3ff2cd9890e20160f472baae7fa629320a90f1b406e9903ef88a7964e3f8c1eb`, 2256 bytes)
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/gh-678b0776161cb8ba38b0ddfe/solve/solve.py` (`ca426a0f526258c7eb9d559b5a9b1d4d9ccdd6d738c84fe46cecd5d4bffb5cb8`, 1380 bytes)
    - `materials/exploit/tictactoe_files/exploit.py` ← `work/materials/pwn-v11/gh-678b0776161cb8ba38b0ddfe/solve/tictactoe_files/exploit.py` (`5f25b94d2c2e10ccf64132c1709525e4a551bea9f9e18458668dedaba296b346`, 3600 bytes)
  - B (1):
    - `materials/deployment/server.py` ← `work/materials/pwn-v11/gh-678b0776161cb8ba38b0ddfe/build/server.py` (`432dedb8311b777191d15a21c3652c79af46f196dce924c939b7d15ba1161886`, 6759 bytes)

### 82. `gh-e871aaabc0ad739c25a49d08` — ppplot

- Identity: lactf / 2024 / Pwn
- Source: `uclaacm/lactf-archive`; `https://github.com/uclaacm/lactf-archive/tree/3379d4a7b36680764a34e7dc817cc3c94c244764/2024/pwn/ppplot`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `bundled_libc_loader`; `heap`
- Selection reason: adds event lactf; adds source uclaacm/lactf-archive
- Material fingerprint: `c760cd752f1e398b580e63d04d624ca2112f232dbc429dbcd8ebe24de9387b82`
- Material paths:
  - A (5):
    - `materials/attachments/ld-linux-x86-64.so.2` ← `work/materials/pwn-v11/gh-e871aaabc0ad739c25a49d08/public/ld-linux-x86-64.so.2` (`9749d47e2eb7b84b48ef24bb6d7f595e5129f96154919b7abb3995053fb20ced`, 191504 bytes)
    - `materials/attachments/libc.so.6` ← `work/materials/pwn-v11/gh-e871aaabc0ad739c25a49d08/public/libc.so.6` (`fa2be2458b59a6123bf561e67b3d5d850431e7d05cacb6435483d1e47eff6de5`, 2029592 bytes)
    - `materials/attachments/ppplot` ← `work/materials/pwn-v11/gh-e871aaabc0ad739c25a49d08/public/ppplot` (`49ab2e270dbc1a313118eff4936b62fb3b668b407d2fe5f8d4fe5ee4a48fcc32`, 14472 bytes)
    - `materials/attachments/ppplot.c` ← `work/materials/pwn-v11/gh-e871aaabc0ad739c25a49d08/public/ppplot.c` (`804b307b6be8eb7f55d781cec58b420a99a4b52454defa44678a69bf7cd52138`, 1996 bytes)
    - `materials/attachments/ppplot_patched` ← `work/materials/pwn-v11/gh-e871aaabc0ad739c25a49d08/public/ppplot_patched` (`d84b67a27054c67f2f14acd32188deb1b8853eda3a0809ccbd2a9647baf963c1`, 20505 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/gh-e871aaabc0ad739c25a49d08/solve/solve.py` (`c80ad41960a0760d403857682c43bb4505b806418736239a254d99e32909ec0b`, 3006 bytes)
  - B (2):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-e871aaabc0ad739c25a49d08/build/Dockerfile` (`9b3b7caf62e3e0736520a246ae6eb4817e40fed876c473977d14bdb9ad43d471`, 233 bytes)
    - `materials/deployment/ppplot.c` ← `work/materials/pwn-v11/gh-e871aaabc0ad739c25a49d08/build/ppplot.c` (`804b307b6be8eb7f55d781cec58b420a99a4b52454defa44678a69bf7cd52138`, 1996 bytes)

### 83. `gh-cce6b5576aab2d5292ff0cb1` — shellc0de-4

- Identity: MicroCTF / 2021 / Pwn
- Source: `Shellmates/MicroCTF-2021-Finals-challs-`; `https://github.com/Shellmates/MicroCTF-2021-Finals-challs-/tree/d579a1495bb689f8b5ccd3e4309b211ae134cbaa/pwn/shellc0de-4`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `system_libc`; `shellcode_seccomp`
- Selection reason: adds event MicroCTF; adds source Shellmates/MicroCTF-2021-Finals-challs-
- Material fingerprint: `04a48829f4c2da33b1b03543003097a0483566e4ffb6adf1359a92b3f5c03829`
- Material paths:
  - A (2):
    - `materials/attachments/shellc0de-4` ← `work/materials/pwn-v11/gh-cce6b5576aab2d5292ff0cb1/public/shellc0de-4` (`cebd4dd4d57cfe58e1f7dd86e2b91125bb1119a9f524d5f2b89ec89856184014`, 24888 bytes)
    - `materials/attachments/shellc0de-4.c` ← `work/materials/pwn-v11/gh-cce6b5576aab2d5292ff0cb1/public/shellc0de-4.c` (`57d9442f3f9ca31d092be4fa439879c078b5b634904abfb757a126457b54abfd`, 17067 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/gh-cce6b5576aab2d5292ff0cb1/writeups/README.md` (`047a2cb6324e9905a315a4baace5edacc2726401c70d031e525d55b18192998d`, 1305 bytes)
  - P (1):
    - `materials/exploit/solution/solve.py` ← `work/materials/pwn-v11/gh-cce6b5576aab2d5292ff0cb1/solve/solution/solve.py` (`70352ce61899fe22f89b46f130465c599a9941caca85fe76763e1d54af5516f6`, 847 bytes)
  - B (5):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-cce6b5576aab2d5292ff0cb1/build/Dockerfile` (`3fead2601a51580835160bf56760348bf60fa054cdf8724d22bbce3b1da80c88`, 324 bytes)
    - `materials/deployment/Makefile` ← `work/materials/pwn-v11/gh-cce6b5576aab2d5292ff0cb1/build/Makefile` (`2a76490844b74163cae87fe3f8d9f63da1f6f3ca74d33169a6d0ab8cdff608d6`, 245 bytes)
    - `materials/deployment/challenge/entrypoint.sh` ← `work/materials/pwn-v11/gh-cce6b5576aab2d5292ff0cb1/build/challenge/entrypoint.sh` (`eee8e1a046473a10bf651cfd700988eb283c2555d8a019ad48c48c6842042139`, 116 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/gh-cce6b5576aab2d5292ff0cb1/build/docker-compose.yml` (`fb79ecf675864bd25229bb25787294db0ff608b01fd40e7293089329f30fcb3b`, 393 bytes)
    - `materials/deployment/src/shellc0de-4.c` ← `work/materials/pwn-v11/gh-cce6b5576aab2d5292ff0cb1/build/src/shellc0de-4.c` (`57d9442f3f9ca31d092be4fa439879c078b5b634904abfb757a126457b54abfd`, 17067 bytes)

### 84. `gh-ff978fd75c915bd5489fc5db` — baby-pwn

- Identity: PCC / 2023 / Pwn
- Source: `AirOverflow/PCC-Challs-Public`; `https://github.com/AirOverflow/PCC-Challs-Public/tree/6a41e0c2e6ae698cd7d487a5eb67b7ee4ea5fd4e/2023/Qualifiers/Pwn/baby-pwn`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `system_libc`; `stack_rop`
- Selection reason: adds event PCC; adds source AirOverflow/PCC-Challs-Public
- Material fingerprint: `6c3b018ca8a1fcbe2a127bbdaf27cab1f51a827ef56151e7cdfea4b8c75b0bd9`
- Material paths:
  - A (4):
    - `materials/attachments/baby-pwn` ← `work/materials/pwn-v11/gh-ff978fd75c915bd5489fc5db/public/baby-pwn` (`07c2a60d8b8fedefb92a022ba179b08b4b9d4a136c2ddf419c50b55c8c8d2d5a`, 17392 bytes)
    - `materials/attachments/baby-pwn.c` ← `work/materials/pwn-v11/gh-ff978fd75c915bd5489fc5db/public/baby-pwn.c` (`e663f19d5c99be674ca9cbcd4ee7faf1c5cb6844251a0fbe0b4c73904e9bd836`, 1547 bytes)
    - `materials/attachments/docker-build.sh` ← `work/materials/pwn-v11/gh-ff978fd75c915bd5489fc5db/public/docker-build.sh` (`a56524c75cb3f18c37718de3c63e6c11964b95a2cad3c2a5393a0e98253522b6`, 59 bytes)
    - `materials/attachments/docker-entrypoint.sh` ← `work/materials/pwn-v11/gh-ff978fd75c915bd5489fc5db/public/docker-entrypoint.sh` (`2a3f56f81fae24ab868488094a3e5b23c556f7ec04bfffab658ea41c9c684c8b`, 833 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/writeup/exploit.py` ← `work/materials/pwn-v11/gh-ff978fd75c915bd5489fc5db/solve/writeup/exploit.py` (`7029f91f6b8dd9d504b3e18b2f1591513518bedab1220ef6257bc673bcba4586`, 470 bytes)
  - B (5):
    - `materials/deployment/src/Dockerfile` ← `work/materials/pwn-v11/gh-ff978fd75c915bd5489fc5db/build/src/Dockerfile` (`510183b2e50e2fee85fe440d8e5a3051f6237c09ed2317e9b039fbde57228ee7`, 258 bytes)
    - `materials/deployment/src/Makefile` ← `work/materials/pwn-v11/gh-ff978fd75c915bd5489fc5db/build/src/Makefile` (`90f1edf11bea5771cb2f99c0383fa0ee329f1403c3d63e8498f089b4e56af004`, 85 bytes)
    - `materials/deployment/src/baby-pwn.c` ← `work/materials/pwn-v11/gh-ff978fd75c915bd5489fc5db/build/src/baby-pwn.c` (`e663f19d5c99be674ca9cbcd4ee7faf1c5cb6844251a0fbe0b4c73904e9bd836`, 1547 bytes)
    - `materials/deployment/src/docker-build.sh` ← `work/materials/pwn-v11/gh-ff978fd75c915bd5489fc5db/build/src/docker-build.sh` (`a56524c75cb3f18c37718de3c63e6c11964b95a2cad3c2a5393a0e98253522b6`, 59 bytes)
    - `materials/deployment/src/docker-entrypoint.sh` ← `work/materials/pwn-v11/gh-ff978fd75c915bd5489fc5db/build/src/docker-entrypoint.sh` (`2a3f56f81fae24ab868488094a3e5b23c556f7ec04bfffab658ea41c9c684c8b`, 833 bytes)

### 85. `saj-2023-pwn-not-malloc` — not_malloc

- Identity: LakeCTF / 2023 / Pwn
- Source: `polygl0ts/lakectf-22-23-public`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/LakeCTF/2023/Quals/pwn/not_malloc`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `bundled_libc_loader`; `heap`, `stack_rop`
- Selection reason: adds event LakeCTF; adds source polygl0ts/lakectf-22-23-public
- Material fingerprint: `4983eb6ce356d0af8abd602ba8061275c91f60ef3028530fdcc9c89a4f3b5131`
- Material paths:
  - A (9):
    - `materials/attachments/README.md` ← `work/materials/pwn-v11/saj-2023-pwn-not-malloc/public/README.md` (`592307865efc2d1536f897e5986a1dce7678b0a1ce7014aba53dc06f5b512df9`, 27 bytes)
    - `materials/attachments/chal` ← `work/materials/pwn-v11/saj-2023-pwn-not-malloc/public/chal` (`ff8e4f086f343e8afd8dd3767c6b990b7305e9d5582cfc132d01e3ddf7069e2f`, 26272 bytes)
    - `materials/attachments/chal.c` ← `work/materials/pwn-v11/saj-2023-pwn-not-malloc/public/chal.c` (`a86bebb79950bdc1c61a2753ef4d80925c948a48c479afb6ce32e384e28ee3bb`, 3110 bytes)
    - `materials/attachments/ld-linux-x86-64.so.2` ← `work/materials/pwn-v11/saj-2023-pwn-not-malloc/public/ld-linux-x86-64.so.2` (`ee7aa16bd8443a946286c9ab84a0af0cbc47aa53a8f00477bf8ada5c38580a36`, 240936 bytes)
    - `materials/attachments/libc.7203acb3.so.6` ← `work/materials/pwn-v11/saj-2023-pwn-not-malloc/public/libc.7203acb3.so.6` (`568740b06a8afa26db4874f8cf61985ecbc6dd127f4229416fe95da8f9ec13fb`, 2216304 bytes)
    - `materials/attachments/libc.so.6` ← `work/materials/pwn-v11/saj-2023-pwn-not-malloc/public/libc.so.6` (`fdaa44be131da64b35f6b132cbb612e0acdd49ca0d29fd247d023619835231e4`, 6616616 bytes)
    - `materials/attachments/libnotmalloc.so` ← `work/materials/pwn-v11/saj-2023-pwn-not-malloc/public/libnotmalloc.so` (`1302c9bb21163f58092205938c62145bd8ecfb3a272fd3834ec309f6be8ad296`, 22984 bytes)
    - `materials/attachments/notmalloc.c` ← `work/materials/pwn-v11/saj-2023-pwn-not-malloc/public/notmalloc.c` (`756bd4cf3e6390e4a60ba437f5fd27d277427cd260af84670e4599893df620cf`, 7662 bytes)
    - `materials/attachments/notmalloc.h` ← `work/materials/pwn-v11/saj-2023-pwn-not-malloc/public/notmalloc.h` (`78954389a4f35def1ec0a10e81aa6b99a22c2464f4e48dc8b5ed4e513d059289`, 349 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2023-pwn-not-malloc/writeups/README.md` (`b3cf61566ce7c58845ec353eb0ee2d4f61ab037c5624a63ba179e143d6e35d3d`, 4903 bytes)
  - P (1):
    - `materials/exploit/working.exploit.py` ← `work/materials/pwn-v11/saj-2023-pwn-not-malloc/solve/working.exploit.py` (`c7b35536246b4d8e26f2d02536487c06ebd08b83ed77be80029eac30dc3a3890`, 3046 bytes)
  - B (4):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2023-pwn-not-malloc/build/Dockerfile` (`7563d7cb6c332f8ce8554738e34f9e7349a54a70b11d6899af17cb62dd9de720`, 446 bytes)
    - `materials/deployment/chal.c` ← `work/materials/pwn-v11/saj-2023-pwn-not-malloc/build/chal.c` (`a86bebb79950bdc1c61a2753ef4d80925c948a48c479afb6ce32e384e28ee3bb`, 3110 bytes)
    - `materials/deployment/notmalloc.c` ← `work/materials/pwn-v11/saj-2023-pwn-not-malloc/build/notmalloc.c` (`756bd4cf3e6390e4a60ba437f5fd27d277427cd260af84670e4599893df620cf`, 7662 bytes)
    - `materials/deployment/notmalloc.h` ← `work/materials/pwn-v11/saj-2023-pwn-not-malloc/build/notmalloc.h` (`78954389a4f35def1ec0a10e81aa6b99a22c2464f4e48dc8b5ed4e513d059289`, 349 bytes)

### 86. `gh-8b033e13b216f7d1fc9da775` — lightspeed

- Identity: c2c / 2026 / Pwn
- Source: `404GH0ST/CTF-Journey`; `https://github.com/404GH0ST/CTF-Journey/tree/5d53385384c914e9c8f1cd3dd86dd0fc352dac48/c2c/2026/pwn/lightspeed`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `bundled_libc_only`; `heap`
- Selection reason: adds event c2c; adds source 404GH0ST/CTF-Journey
- Material fingerprint: `739a41b3cbeacc3616ba18ad5bc8e8215d717e328c9ad633a25df142d30290aa`
- Material paths:
  - A (7):
    - `materials/attachments/a.js` ← `work/materials/pwn-v11/gh-8b033e13b216f7d1fc9da775/public/a.js` (`32b77795df33a2a557c1c22eaa06e098037b42f0375761ac178cb039b9e74b3d`, 2985 bytes)
    - `materials/attachments/getflag` ← `work/materials/pwn-v11/gh-8b033e13b216f7d1fc9da775/public/getflag` (`c4263d378b8cf15067f86897e2137711fda2e44d65a26ca658727558c529af1e`, 45 bytes)
    - `materials/attachments/libc.so.6` ← `work/materials/pwn-v11/gh-8b033e13b216f7d1fc9da775/public/libc.so.6` (`06e87bc6946702848d7f6aeb7e3759ca904458efd8c3ded85ca63099944181ed`, 1999312 bytes)
    - `materials/attachments/patch.diff` ← `work/materials/pwn-v11/gh-8b033e13b216f7d1fc9da775/public/patch.diff` (`f0d7352987c2be5558847459e02cedfeb1d09933dd53a2c7e0e82754a074a0a0`, 3133 bytes)
    - `materials/attachments/qjs` ← `work/materials/pwn-v11/gh-8b033e13b216f7d1fc9da775/public/qjs` (`dea95f737a84019dfa3a500fa13974733dfd3ca0fb8d0b841f7c2a97e35b31f1`, 1296592 bytes)
    - `materials/attachments/run.py` ← `work/materials/pwn-v11/gh-8b033e13b216f7d1fc9da775/public/run.py` (`534b0a1d569070044a28874e2f5e029e2538f64ecd482aad3e3bc6b3b7b6ca32`, 1076 bytes)
    - `materials/attachments/test.js` ← `work/materials/pwn-v11/gh-8b033e13b216f7d1fc9da775/public/test.js` (`b0db80202ccbf75c8f626caf906559f7543e243bda19f260891786eb06ab55fc`, 255 bytes)
  - W: absent
  - P (3):
    - `materials/exploit/exploit.js` ← `work/materials/pwn-v11/gh-8b033e13b216f7d1fc9da775/solve/exploit.js` (`32b77795df33a2a557c1c22eaa06e098037b42f0375761ac178cb039b9e74b3d`, 2985 bytes)
    - `materials/exploit/poc.js` ← `work/materials/pwn-v11/gh-8b033e13b216f7d1fc9da775/solve/poc.js` (`57b7ecfea49f5213175b511f69ec209ab9483366902c6272c94fa7757d930eeb`, 526 bytes)
    - `materials/exploit/poc_refcount.c` ← `work/materials/pwn-v11/gh-8b033e13b216f7d1fc9da775/solve/poc_refcount.c` (`a2776c3d3cfec20325afad59735e58f542c81c59e22162901e1ed7eb491bd225`, 615 bytes)
  - B (4):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-8b033e13b216f7d1fc9da775/build/Dockerfile` (`e1d08c9cc5392155e30ce679554dbe4381fb0692c1cc93773498c3596de35211`, 338 bytes)
    - `materials/deployment/a.js` ← `work/materials/pwn-v11/gh-8b033e13b216f7d1fc9da775/build/a.js` (`32b77795df33a2a557c1c22eaa06e098037b42f0375761ac178cb039b9e74b3d`, 2985 bytes)
    - `materials/deployment/run.py` ← `work/materials/pwn-v11/gh-8b033e13b216f7d1fc9da775/build/run.py` (`534b0a1d569070044a28874e2f5e029e2538f64ecd482aad3e3bc6b3b7b6ca32`, 1076 bytes)
    - `materials/deployment/test.js` ← `work/materials/pwn-v11/gh-8b033e13b216f7d1fc9da775/build/test.js` (`b0db80202ccbf75c8f626caf906559f7543e243bda19f260891786eb06ab55fc`, 255 bytes)

### 87. `saj-2023-pwn-flight` — flight

- Identity: BSidesSF / 2023 / Pwn
- Source: `BSidesSF/ctf-2023-release`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/BSidesSF/2023/pwn/flight`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `system_libc`; `other`
- Selection reason: adds event BSidesSF; adds source BSidesSF/ctf-2023-release
- Material fingerprint: `9cc91b984a0e42653c6d2558c229c9dac48f197935867ddf607fbcbdb707799e`
- Material paths:
  - A (4):
    - `materials/attachments/flight` ← `work/materials/pwn-v11/saj-2023-pwn-flight/public/flight` (`7f7338a8aeb80f4b4879447de31029a4ee12de8491b55838fc3070ab19081604`, 16192 bytes)
    - `materials/attachments/flight.321f80e9` ← `work/materials/pwn-v11/saj-2023-pwn-flight/public/flight.321f80e9` (`f3e6c45fd5580624dea2f42130aa1fa5871d113b20608fdbb65f7260512f0959`, 16196 bytes)
    - `materials/attachments/main.c` ← `work/materials/pwn-v11/saj-2023-pwn-flight/public/main.c` (`aee089d7ae846b73526e75bca502cf026bc5d230f9c970b62fa7c0229a36d2e1`, 1566 bytes)
    - `materials/attachments/metadata.yml` ← `work/materials/pwn-v11/saj-2023-pwn-flight/public/metadata.yml` (`d3600afd04126e715ae705fdf1ebe4f5725db22a32483d370507055c751ef98a`, 242 bytes)
  - W (1):
    - `materials/writeups/Flight.md` ← `work/materials/pwn-v11/saj-2023-pwn-flight/writeups/Flight.md` (`3cf1ac141e53fbfe7c8844414689181188d553b3529db98c21e1da2982dc8f00`, 15554 bytes)
  - P (1):
    - `materials/exploit/solution/exploit.py` ← `work/materials/pwn-v11/saj-2023-pwn-flight/solve/solution/exploit.py` (`94817a6dbd7e906072077efc25ed93fffe5e69fb4b2a4928afe9b4dec6f1c6d6`, 484 bytes)
  - B (3):
    - `materials/deployment/challenge/Dockerfile` ← `work/materials/pwn-v11/saj-2023-pwn-flight/build/challenge/Dockerfile` (`7e26c870c7ea8ee9387490ff235f3e3ccf8c977d83d70c3226b714a7a45c2c25`, 443 bytes)
    - `materials/deployment/challenge/main.c` ← `work/materials/pwn-v11/saj-2023-pwn-flight/build/challenge/main.c` (`aee089d7ae846b73526e75bca502cf026bc5d230f9c970b62fa7c0229a36d2e1`, 1566 bytes)
    - `materials/deployment/challenge/makefile` ← `work/materials/pwn-v11/saj-2023-pwn-flight/build/challenge/makefile` (`ea300959564e77ca5b61bc879fa62aa1e06c658d1783186902248f15f7808d25`, 81 bytes)

### 88. `gh-c04dcf77cc7aa15234389efb` — secret

- Identity: BITSkrieg InductionCTF / 2025 / Pwn
- Source: `harshulvijay/BITSkrieg-InductionCTF-2025`; `https://github.com/harshulvijay/BITSkrieg-InductionCTF-2025/tree/513c855c0d75fe5852dd4716c9104335bec095ab/PWN/secret`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `source_build`; `unknown_or_non_elf`; `other`
- Selection reason: adds event BITSkrieg InductionCTF; adds source harshulvijay/BITSkrieg-InductionCTF-2025
- Material fingerprint: `acc4db3b8863afd40a378dee7b1523a9196e64239d1178e86eafd29f72a4f8a1`
- Material paths:
  - A (1):
    - `materials/attachments/Secret.c` ← `work/materials/pwn-v11/gh-c04dcf77cc7aa15234389efb/public/Secret.c` (`c3b9e23d5f3b5d8a7e269978446d4c8f749265db14aebdef55e257446a1db846`, 925 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/gh-c04dcf77cc7aa15234389efb/solve/solve.py` (`fcb4bfd738b6f26e3858e5dd87a12c2cfbf8a5935352407b89e46254d9a91c6a`, 177 bytes)
  - B (2):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-c04dcf77cc7aa15234389efb/build/Dockerfile` (`62fcdb51db69e5ac65c327280fe6a7fc196cb9517a63d7b85f5441f2d8569d0c`, 257 bytes)
    - `materials/deployment/Secret.c` ← `work/materials/pwn-v11/gh-c04dcf77cc7aa15234389efb/build/Secret.c` (`c3b9e23d5f3b5d8a7e269978446d4c8f749265db14aebdef55e257446a1db846`, 925 bytes)

### 89. `saj-2026-pwn-basalt-chamber` — Basalt_Chamber

- Identity: 0xV01D / 2026 / Pwn
- Source: `0xlast500-0xV01D/0xV01D-CTF`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/0xV01D/2026/pwn/Basalt_Chamber`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `static`; `shellcode_seccomp`
- Selection reason: adds event 0xV01D; adds source 0xlast500-0xV01D/0xV01D-CTF
- Material fingerprint: `e0740007f434cd0ddc482710b17ff73cab78369a8869c12060c627cc672a04a2`
- Material paths:
  - A (3):
    - `materials/attachments/README_NOTE.txt` ← `work/materials/pwn-v11/saj-2026-pwn-basalt-chamber/public/README_NOTE.txt` (`63caba7997946c619f8be28275e6f4c1593c77345827388c40f6e2bb498a9038`, 101 bytes)
    - `materials/attachments/blackglass_sandbox` ← `work/materials/pwn-v11/saj-2026-pwn-basalt-chamber/public/blackglass_sandbox` (`e28ae13c6f288ca7aece2b8f8639435c53bb88079a89c3bd05473eb8d2bb6e8b`, 706312 bytes)
    - `materials/attachments/seccomp_policy.txt` ← `work/materials/pwn-v11/saj-2026-pwn-basalt-chamber/public/seccomp_policy.txt` (`7d263c5591ac297be380542fe44ee06571b07347d0699a03864bc4e2a48a25bd`, 258 bytes)
  - W (2):
    - `materials/writeups/solution.md` ← `work/materials/pwn-v11/saj-2026-pwn-basalt-chamber/writeups/solution.md` (`05a19efaa76e7886ce05beb9175eafc5f23de461c03377e1f0c35bd608363ba8`, 3854 bytes)
    - `materials/writeups/solution_zh.md` ← `work/materials/pwn-v11/saj-2026-pwn-basalt-chamber/writeups/solution_zh.md` (`e3af556647084be09bac0fae41d5e7a1032738cf588e290750f70f5e7671f4c7`, 3719 bytes)
  - P (2):
    - `materials/exploit/solution.d8bed422.py` ← `work/materials/pwn-v11/saj-2026-pwn-basalt-chamber/solve/solution.d8bed422.py` (`706b1201c86a746a8e01966a84a7f883ac7f18bbc2a292e8bd3400c67b6a74c6`, 549 bytes)
    - `materials/exploit/solution.py` ← `work/materials/pwn-v11/saj-2026-pwn-basalt-chamber/solve/solution.py` (`e51f8c46d216af67cb7dc1eb86aaa1e82e0ed781dfc13b8b56cbf36b4e96f208`, 4032 bytes)
  - B (2):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2026-pwn-basalt-chamber/build/Dockerfile` (`e74bcfba28a113601c3e5d9a0c0f4fdaf576f32d6c23a9aa3e2c9031e531eebf`, 340 bytes)
    - `materials/deployment/run.sh` ← `work/materials/pwn-v11/saj-2026-pwn-basalt-chamber/build/run.sh` (`e576c3252d1fb3be859efb0981ea4e8ff67a3492dab79eed0a561de74569dc1b`, 105 bytes)

### 90. `gh-6693bed7813ad54b06193d00` — signal

- Identity: cscctf / 2019 / Pwn
- Source: `bmleeBigby/cscctf`; `https://github.com/bmleeBigby/cscctf/tree/37e2888dd7fbf30969e236b2e51868b236eadc5a/2019/qual/pwn/signal`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile_compose`; `source_build`; `bundled_libc_only`; `shellcode_seccomp`
- Selection reason: adds event cscctf; adds source bmleeBigby/cscctf
- Material fingerprint: `e2e8f142f0af125552e423db6706c9d15fdb1fa919530393c9bd55b910ed8438`
- Material paths:
  - A (3):
    - `materials/attachments/libc-2.27.so` ← `work/materials/pwn-v11/gh-6693bed7813ad54b06193d00/public/libc-2.27.so` (`cd7c1a035d24122798d97a47a10f6e2b71d58710aecfd392375f1aa9bdde164d`, 2030544 bytes)
    - `materials/attachments/signal.c` ← `work/materials/pwn-v11/gh-6693bed7813ad54b06193d00/public/signal.c` (`4cc1a7a684bcc924b8f3958c683d0aaee1205727bdc3386fff53c44de97e9bb0`, 278 bytes)
    - `materials/attachments/startchall.sh` ← `work/materials/pwn-v11/gh-6693bed7813ad54b06193d00/public/startchall.sh` (`9e8aed213431150445387106dca797b666f2e5dfd42dcaf4e723212ca5b69121`, 52 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/exploit.py` ← `work/materials/pwn-v11/gh-6693bed7813ad54b06193d00/solve/exploit.py` (`73b5ced5b3a9e94381e07db0f07e6bd5922927f9434268f19135221c8394e4e2`, 1459 bytes)
  - B (5):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-6693bed7813ad54b06193d00/build/Dockerfile` (`95fe8ec0fb4df924cb19b3905c4bfd32a07604adb0488689bf74ecd0fc69d8cd`, 290 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/gh-6693bed7813ad54b06193d00/build/docker-compose.yml` (`2e0dec964ba1acc8385b4b4024f5bab6c751b4f8e4b0f33465539d618adac30d`, 330 bytes)
    - `materials/deployment/signal.c` ← `work/materials/pwn-v11/gh-6693bed7813ad54b06193d00/build/signal.c` (`4cc1a7a684bcc924b8f3958c683d0aaee1205727bdc3386fff53c44de97e9bb0`, 278 bytes)
    - `materials/deployment/startchall.sh` ← `work/materials/pwn-v11/gh-6693bed7813ad54b06193d00/build/startchall.sh` (`9e8aed213431150445387106dca797b666f2e5dfd42dcaf4e723212ca5b69121`, 52 bytes)
    - `materials/deployment/xinetd` ← `work/materials/pwn-v11/gh-6693bed7813ad54b06193d00/build/xinetd` (`b66a0660e882d574be7fbb4e65909f7a548cd075b77147edebf0fc9f8dd2b7fd`, 207 bytes)

### 91. `gh-2f68232a08e0468a2f79d392` — basalt-chamber

- Identity: 0xvoidCTF / 2026 / Pwn
- Source: `silentzero192/CTFtime-Writeups`; `https://github.com/silentzero192/CTFtime-Writeups/tree/af65fe46598245a0ff1594e59fc906bde5675833/2026/0xvoidCTF-2026/pwn/basalt-chamber`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `static`; `shellcode_seccomp`
- Selection reason: adds event 0xvoidCTF; adds source silentzero192/CTFtime-Writeups
- Material fingerprint: `a0235131d1c7356725b892d9bd2d5c6226cbef8cfceebf0434faf12db4d0e5f1`
- Material paths:
  - A (3):
    - `materials/attachments/README_NOTE.txt` ← `work/materials/pwn-v11/gh-2f68232a08e0468a2f79d392/public/README_NOTE.txt` (`63caba7997946c619f8be28275e6f4c1593c77345827388c40f6e2bb498a9038`, 101 bytes)
    - `materials/attachments/blackglass_sandbox` ← `work/materials/pwn-v11/gh-2f68232a08e0468a2f79d392/public/blackglass_sandbox` (`e28ae13c6f288ca7aece2b8f8639435c53bb88079a89c3bd05473eb8d2bb6e8b`, 706312 bytes)
    - `materials/attachments/seccomp_policy.txt` ← `work/materials/pwn-v11/gh-2f68232a08e0468a2f79d392/public/seccomp_policy.txt` (`7d263c5591ac297be380542fe44ee06571b07347d0699a03864bc4e2a48a25bd`, 258 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/gh-2f68232a08e0468a2f79d392/writeups/README.md` (`38deb3b90f18f523fa7173dadd36e537926bd3f50b57e944d1c85ef559aa0215`, 14207 bytes)
  - P (1):
    - `materials/exploit/solution.py` ← `work/materials/pwn-v11/gh-2f68232a08e0468a2f79d392/solve/solution.py` (`e51f8c46d216af67cb7dc1eb86aaa1e82e0ed781dfc13b8b56cbf36b4e96f208`, 4032 bytes)
  - B (3):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-2f68232a08e0468a2f79d392/build/Dockerfile` (`e74bcfba28a113601c3e5d9a0c0f4fdaf576f32d6c23a9aa3e2c9031e531eebf`, 340 bytes)
    - `materials/deployment/run.sh` ← `work/materials/pwn-v11/gh-2f68232a08e0468a2f79d392/build/run.sh` (`e576c3252d1fb3be859efb0981ea4e8ff67a3492dab79eed0a561de74569dc1b`, 105 bytes)
    - `materials/deployment/solution.py` ← `work/materials/pwn-v11/gh-2f68232a08e0468a2f79d392/build/solution.py` (`e51f8c46d216af67cb7dc1eb86aaa1e82e0ed781dfc13b8b56cbf36b4e96f208`, 4032 bytes)

### 92. `gh-446daaef67eaba77fdcfc088` — target practice

- Identity: CSAW CTF / 2023 / Pwn
- Source: `osirislab/CSAW-CTF-2023-Quals`; `https://github.com/osirislab/CSAW-CTF-2023-Quals/tree/93d8266d6f267e16db850d239629ddfec3fed405/pwn/target practice`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `source_build`; `unknown_or_non_elf`; `other`
- Selection reason: adds event CSAW CTF; adds source osirislab/CSAW-CTF-2023-Quals
- Material fingerprint: `15c5c3a265e5c9ba6959d30cc476a65ca1ee69c120bf9c174d8c8e8a7f3e53bd`
- Material paths:
  - A (2):
    - `materials/attachments/challenge.json` ← `work/materials/pwn-v11/gh-446daaef67eaba77fdcfc088/public/challenge.json` (`76908708ca3f405ceaaadffcfca47cfd30a3a65566efd3a72982b39dfd0656d9`, 290 bytes)
    - `materials/attachments/target_practice.c` ← `work/materials/pwn-v11/gh-446daaef67eaba77fdcfc088/public/target_practice.c` (`a5d8f83b66bfcfe7115aab4dbc43610a384475e08283b9986eab888cc9a901ff`, 420 bytes)
  - W: absent
  - P (2):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/gh-446daaef67eaba77fdcfc088/solve/solve.py` (`e462f102341c24262510c80c63d72c313b2d17046c0cc556901d678dd6e4acd0`, 91 bytes)
    - `materials/exploit/solve.txt` ← `work/materials/pwn-v11/gh-446daaef67eaba77fdcfc088/solve/solve.txt` (`db40b33b1f78301c1826513e63626cf6cc61ede4fc7d65a06399169a86fda1e1`, 176 bytes)
  - B (3):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-446daaef67eaba77fdcfc088/build/Dockerfile` (`fb4ce4497f10783b502733b6e1f053e54f7e9a3596e946af6dc88ecb57d3417b`, 552 bytes)
    - `materials/deployment/Makefile` ← `work/materials/pwn-v11/gh-446daaef67eaba77fdcfc088/build/Makefile` (`ba6a1b8f8016184006b020539f2b0835f571b1ac2cd8c0f3e0ee428800e4ec14`, 100 bytes)
    - `materials/deployment/target_practice.c` ← `work/materials/pwn-v11/gh-446daaef67eaba77fdcfc088/build/target_practice.c` (`a5d8f83b66bfcfe7115aab4dbc43610a384475e08283b9986eab888cc9a901ff`, 420 bytes)

### 93. `saj-2024-pwn-bytecode` — Bytecode

- Identity: Akasec / 2024 / Pwn
- Source: `Akasec-1337/Akasec-CTF-2024`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/Akasec/2024/pwn/Bytecode`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `bundled_libc_loader`; `heap`, `shellcode_seccomp`, `vm_emulator`
- Selection reason: adds event Akasec; adds source Akasec-1337/Akasec-CTF-2024
- Material fingerprint: `c8607e1310f190a21051353c8e3f472926bb364ab5bf1a614d1449c067eae7bd`
- Material paths:
  - A (11):
    - `materials/attachments/bytecode` ← `work/materials/pwn-v11/saj-2024-pwn-bytecode/public/bytecode` (`fb8d12296c0fa7c3c6a2203e8fd7d200fb4066b471bb11cebb8d967fd3e0e33a`, 16648 bytes)
    - `materials/attachments/bytecode.__dir__.8e896187/main.c` ← `work/materials/pwn-v11/saj-2024-pwn-bytecode/public/bytecode.__dir__.8e896187/main.c` (`b8a639cabd063a922a5528d600b6e1cdefa27f9f767af4026fc4e24403aa7e7c`, 4904 bytes)
    - `materials/attachments/bytecode_patched` ← `work/materials/pwn-v11/saj-2024-pwn-bytecode/public/bytecode_patched` (`bd329c7cd1205e8e954b4bceb1e0f8a24447cd80883b6957964721cbe4a2de47`, 24416 bytes)
    - `materials/attachments/helloworld.png` ← `work/materials/pwn-v11/saj-2024-pwn-bytecode/public/helloworld.png` (`d9a5b551ec33d44c2311ae950e7739dd81bcbf2a392738beb6cf2c65b1f469c9`, 3724 bytes)
    - `materials/attachments/ld-linux-x86-64.so.2` ← `work/materials/pwn-v11/saj-2024-pwn-bytecode/public/ld-linux-x86-64.so.2` (`b7695da977e205398b33922d61493cc1e436cd2321bb2e54fbdc39b95fabeff7`, 236616 bytes)
    - `materials/attachments/libc.so.6` ← `work/materials/pwn-v11/saj-2024-pwn-bytecode/public/libc.so.6` (`fc4c52f3910ed57a088d19ab86c671358f5e917cd4e95b21fd08e4fd922c0aa2`, 2125328 bytes)
    - `materials/attachments/libc_leak.png` ← `work/materials/pwn-v11/saj-2024-pwn-bytecode/public/libc_leak.png` (`dd371a2925b51e8bacf7cfd84ed2c12876df068fc97c25a5c09b152c54fd09d7`, 30197 bytes)
    - `materials/attachments/program.png` ← `work/materials/pwn-v11/saj-2024-pwn-bytecode/public/program.png` (`974eedb92e0be5b64a274bb8e0a64ed907d19a5b6f6cfb8a80b220fa1bd89140`, 15452 bytes)
    - `materials/attachments/stack_mem.png` ← `work/materials/pwn-v11/saj-2024-pwn-bytecode/public/stack_mem.png` (`9bda8f8da3835a14f5ad9165add784e16258c64e472289e3484e174f2efd7671`, 109040 bytes)
    - `materials/attachments/targets.png` ← `work/materials/pwn-v11/saj-2024-pwn-bytecode/public/targets.png` (`e1202258e1d231f8a9177708002e888e184882e265b713482067c568a5b3c079`, 74583 bytes)
    - `materials/attachments/x.py` ← `work/materials/pwn-v11/saj-2024-pwn-bytecode/public/x.py` (`f31d25a02b962f2114cdc921427fc31da4e18576570b13c135696e141086851c`, 4412 bytes)
  - W (2):
    - `materials/writeups/README.2b05004b.md` ← `work/materials/pwn-v11/saj-2024-pwn-bytecode/writeups/README.2b05004b.md` (`674bd64c5af8a49934c281bed2c1f5df7a3fb1aadbfb947992efa3b2e49e949a`, 21326 bytes)
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2024-pwn-bytecode/writeups/README.md` (`05d6299ea9533f993fda71b535155378bb551df09618dbd8d0dc70c0cf49ef02`, 1847 bytes)
  - P (2):
    - `materials/exploit/images/solve.png` ← `work/materials/pwn-v11/saj-2024-pwn-bytecode/solve/images/solve.png` (`23f8a15737ac5da9cf5d3173e2c6bbfc7427da928a8566898a9008745fe72fe3`, 78744 bytes)
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2024-pwn-bytecode/solve/solve.py` (`dffb9ca9462bf4d0d1e190a91958dab132a03f1f11841d0df6f4f6ff4b513f9c`, 3200 bytes)
  - B (3):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2024-pwn-bytecode/build/Dockerfile` (`ff16bd47aad2009bd92ead688e8568a4821777df0f7165e0eeaea7cc57b6734a`, 287 bytes)
    - `materials/deployment/main.c` ← `work/materials/pwn-v11/saj-2024-pwn-bytecode/build/main.c` (`b8a639cabd063a922a5528d600b6e1cdefa27f9f767af4026fc4e24403aa7e7c`, 4904 bytes)
    - `materials/deployment/makefile` ← `work/materials/pwn-v11/saj-2024-pwn-bytecode/build/makefile` (`028260b305776c72086ea400693fcfb0822d4b806954b90d363a122cd4db792b`, 142 bytes)

### 94. `gh-86e6f6e031779e125dce97a3` — intact

- Identity: magpieCTF / 2022 / Pwn
- Source: `infosec-ucalgary/magpieCTF2022-public`; `https://github.com/infosec-ucalgary/magpieCTF2022-public/tree/9f662015e374b03431ae26ee9dc5149176ccc92f/challenges/binary-exploitation/intact`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile`; `hybrid`; `system_libc`; `other`
- Selection reason: adds event magpieCTF; adds source infosec-ucalgary/magpieCTF2022-public
- Material fingerprint: `993cc3e0d55232bfdfc4f3787172db8af0eb68fd5b3a83d0937fec8c96ac93b7`
- Material paths:
  - A (3):
    - `materials/attachments/intact` ← `work/materials/pwn-v11/gh-86e6f6e031779e125dce97a3/public/intact` (`c0fc416d06c947646ccc2e834ea55ac56aeae4addb085af78ea0ce179d09d955`, 16712 bytes)
    - `materials/attachments/intact.265b603c` ← `work/materials/pwn-v11/gh-86e6f6e031779e125dce97a3/public/intact.265b603c` (`db40ae5bcf93e782237f468292a14208c4732552af896cfb86a8797d2101418c`, 16672 bytes)
    - `materials/attachments/intact.c` ← `work/materials/pwn-v11/gh-86e6f6e031779e125dce97a3/public/intact.c` (`baa61dc30284d67b2f4ce6336c9e4961aa5c79c4cd481cd5a18c49d2152ff6b8`, 1359 bytes)
  - W: absent
  - P (2):
    - `materials/exploit/exploit.py` ← `work/materials/pwn-v11/gh-86e6f6e031779e125dce97a3/solve/exploit.py` (`0efa8b2dc58a1c69fe58e592335823a280f731a69db9d30cd843569cb9cabd97`, 1869 bytes)
    - `materials/exploit/solve/exploit.py` ← `work/materials/pwn-v11/gh-86e6f6e031779e125dce97a3/solve/solve/exploit.py` (`568689b6831ad94856e1ae968c5c66e7b420bb2bfded39a298edc52ddac398e0`, 443 bytes)
  - B (3):
    - `materials/deployment/source/Dockerfile` ← `work/materials/pwn-v11/gh-86e6f6e031779e125dce97a3/build/source/Dockerfile` (`a44f4a38e9a1a5bd320f549ad7c819130c8415f01454a3a38f5f97a96d620e67`, 637 bytes)
    - `materials/deployment/source/app/Makefile` ← `work/materials/pwn-v11/gh-86e6f6e031779e125dce97a3/build/source/app/Makefile` (`9588f11d132172829739394abf117c7a5a2e49336e0f3cfdcefddd8fac00e2b7`, 102 bytes)
    - `materials/deployment/source/app/intact.c` ← `work/materials/pwn-v11/gh-86e6f6e031779e125dce97a3/build/source/app/intact.c` (`baa61dc30284d67b2f4ce6336c9e4961aa5c79c4cd481cd5a18c49d2152ff6b8`, 1359 bytes)

### 95. `saj-2023-pwn-champions-heap` — Champions_Heap

- Identity: BSidesAlgiers / 2023 / Pwn
- Source: `Shellmates/BSides-Algiers-2025-challenges`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/BSidesAlgiers/2023/pwn/Champions_Heap`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `bundled_libc_loader`; `heap`, `shellcode_seccomp`, `stack_rop`
- Selection reason: adds event BSidesAlgiers; adds source Shellmates/BSides-Algiers-2025-challenges
- Material fingerprint: `13eaede0a72bf7d645cd7e2ac79522bc6b2bb1c7e92206d86e0fa3d680d2274a`
- Material paths:
  - A (5):
    - `materials/attachments/champions-heap` ← `work/materials/pwn-v11/saj-2023-pwn-champions-heap/public/champions-heap` (`14c1dc57517c8b8bf5251b1c76f16f77f1cf695dc9fdf9539e3b17b1a66500e2`, 18160 bytes)
    - `materials/attachments/champions-heap.c` ← `work/materials/pwn-v11/saj-2023-pwn-champions-heap/public/champions-heap.c` (`586ab2a1cf4fee05299549be25b49d3f29bcdfd9d6f3a4978f09eb9b189d4128`, 5833 bytes)
    - `materials/attachments/ld-linux-x86-64.so.2` ← `work/materials/pwn-v11/saj-2023-pwn-champions-heap/public/ld-linux-x86-64.so.2` (`da5e0c515d6536d59ce5c100ac5359e7f5a5a354f60eeff369a378ba2c80fdcb`, 179152 bytes)
    - `materials/attachments/libc.so.6` ← `work/materials/pwn-v11/saj-2023-pwn-champions-heap/public/libc.so.6` (`38ef7517c9272086865391f855bd52a96712cdf1db942c0d899c9600e4b2173d`, 17890352 bytes)
    - `materials/attachments/libseccomp.so.2` ← `work/materials/pwn-v11/saj-2023-pwn-champions-heap/public/libseccomp.so.2` (`cdf4d186e965b23bbeb604ff8b449fcbf1af0b09fffb29e74e930ec8ca6cd83a`, 129312 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/saj-2023-pwn-champions-heap/writeups/README.md` (`3a1d0bff8e0ae51e9b0e1c23f1a1ef1fb89cab54cc9869ccd78d7dc38a743c9d`, 61 bytes)
  - P (1):
    - `materials/exploit/solution/solve.py` ← `work/materials/pwn-v11/saj-2023-pwn-champions-heap/solve/solution/solve.py` (`efc0b179af2fd014b8fea4e6ebb14beb6c76ddaed6894366729077345e5b7cce`, 8651 bytes)
  - B (5):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2023-pwn-champions-heap/build/Dockerfile` (`1552a3497882fee1a3720601298a04317954a5b44f5b7eb73c482aa5f9b71c3c`, 348 bytes)
    - `materials/deployment/Makefile` ← `work/materials/pwn-v11/saj-2023-pwn-champions-heap/build/Makefile` (`83c39f76ffa7f704979e70100031f3629c564e8d9cf890999b1778402da3ea1b`, 217 bytes)
    - `materials/deployment/challenge/entrypoint.sh` ← `work/materials/pwn-v11/saj-2023-pwn-champions-heap/build/challenge/entrypoint.sh` (`d9d1721243ad4f9dd2c51519abc6a971c3d7e0fd3ba3659e3da93181b6b307a3`, 119 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/saj-2023-pwn-champions-heap/build/docker-compose.yml` (`59b61dbb8c158c10f7a38786a0ecd006be70bb4f68dec0e96218ddddf4e11781`, 366 bytes)
    - `materials/deployment/src/champions-heap.c` ← `work/materials/pwn-v11/saj-2023-pwn-champions-heap/build/src/champions-heap.c` (`586ab2a1cf4fee05299549be25b49d3f29bcdfd9d6f3a4978f09eb9b189d4128`, 5833 bytes)

### 96. `gh-91b6f2c11338e3f2bde7f926` — ret2win4

- Identity: Friendly CTF / 2024 / Pwn
- Source: `securinets-insat/Friendly-CTF-2024`; `https://github.com/securinets-insat/Friendly-CTF-2024/tree/6535e0782a956af7a1f84f227d1c63189bc73a52/Pwn/ret2win4`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `system_libc`; `stack_rop`
- Selection reason: adds event Friendly CTF; adds source securinets-insat/Friendly-CTF-2024
- Material fingerprint: `77b3b3dd1a80a8d0bc519e3db2afaea432f3a56731cd4a689b3fe455812ef82b`
- Material paths:
  - A (2):
    - `materials/attachments/main` ← `work/materials/pwn-v11/gh-91b6f2c11338e3f2bde7f926/public/main` (`56fb5c2ac39d25e1887be0ed5e499ef9d0241351d8971056f6277166afb1ed48`, 16552 bytes)
    - `materials/attachments/main.c` ← `work/materials/pwn-v11/gh-91b6f2c11338e3f2bde7f926/public/main.c` (`7bc7bcab1a4fd202e9474fca82988844ac6bc33a79d14562aff4aae5e80761e6`, 1753 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/gh-91b6f2c11338e3f2bde7f926/solve/solve.py` (`798f1af209b363e62468537ce122835d01b4040d7339e3644ca38ddc48416ce6`, 360 bytes)
  - B (3):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-91b6f2c11338e3f2bde7f926/build/Dockerfile` (`2c743e85cd017e3babcf7b863bf5b76ed79969151fb66abc7c76bff6b7be4385`, 307 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/gh-91b6f2c11338e3f2bde7f926/build/docker-compose.yml` (`e5bf6fb34b97be330a3ec45985ab70a2c6314d13e32ac63971f611eaaf56c464`, 268 bytes)
    - `materials/deployment/main.c` ← `work/materials/pwn-v11/gh-91b6f2c11338e3f2bde7f926/build/main.c` (`7bc7bcab1a4fd202e9474fca82988844ac6bc33a79d14562aff4aae5e80761e6`, 1753 bytes)

### 97. `gh-69a56364382cede9b3074e69` — Empire Server

- Identity: PolyPwnCTF / 2025 / Pwn
- Source: `polycyber/PolyPwnCTF-2025-Challenges`; `https://github.com/polycyber/PolyPwnCTF-2025-Challenges/tree/f6bc3ad072d55150117738741d454ef1f0c76f8b/Pwn/Empire Server`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile`; `source_build`; `unknown_or_non_elf`; `shellcode_seccomp`
- Selection reason: adds event PolyPwnCTF; adds source polycyber/PolyPwnCTF-2025-Challenges
- Material fingerprint: `8c7fe9079fe95377d21accdc568ed0adf1190c0cbb62df95158d033e4823851a`
- Material paths:
  - A (8):
    - `materials/attachments/src_code/src/main.c` ← `work/materials/pwn-v11/gh-69a56364382cede9b3074e69/public/src_code/src/main.c` (`df09a45c177183d1298e128ef1b8581f6aa5625a485b77c010deaf92aeaa6885`, 8541 bytes)
    - `materials/attachments/src_code/www/admin.html` ← `work/materials/pwn-v11/gh-69a56364382cede9b3074e69/public/src_code/www/admin.html` (`ebe365818d60035dad77954df805323219e986703c1f37450d4c4bd3305535c3`, 2412 bytes)
    - `materials/attachments/src_code/www/bad_login.html` ← `work/materials/pwn-v11/gh-69a56364382cede9b3074e69/public/src_code/www/bad_login.html` (`b29e5fe14809dd9d04285ec90625e9307312cf73f91eccfcf91efa8cb073d8c7`, 47 bytes)
    - `materials/attachments/src_code/www/index.html` ← `work/materials/pwn-v11/gh-69a56364382cede9b3074e69/public/src_code/www/index.html` (`13d0e717feb4dbde88fb63fde6702006364b2d40af7f992f40abc3e5d0f07854`, 1949 bytes)
    - `materials/attachments/src_code/www/login.html` ← `work/materials/pwn-v11/gh-69a56364382cede9b3074e69/public/src_code/www/login.html` (`6173dacfdd2cba5dd2c4a619ac33f3b79bb57b95aaaa48c10a4388161d4483eb`, 3037 bytes)
    - `materials/attachments/src_code/www/style.css` ← `work/materials/pwn-v11/gh-69a56364382cede9b3074e69/public/src_code/www/style.css` (`572800f3893e9733acf9d8b065ca768e2902b684a04ef9fc55d4a700302f386a`, 779 bytes)
    - `materials/attachments/src_code/www/video.mp4` ← `work/materials/pwn-v11/gh-69a56364382cede9b3074e69/public/src_code/www/video.mp4` (`c26aafd04865cae882294ee139ee03827e392a5d2add0e1f34b1353bc3a20285`, 7150169 bytes)
    - `materials/attachments/start_services.sh` ← `work/materials/pwn-v11/gh-69a56364382cede9b3074e69/public/start_services.sh` (`a85fb88f6543ffb94d2677f0870850ebbdbd4921c013bfd7dc38147807201555`, 185 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/gh-69a56364382cede9b3074e69/writeups/README.md` (`17608f4d9d52e76e1dcef5922907c163829a1ef1435cb6dc83edf09c3f1da299`, 10665 bytes)
  - P (1):
    - `materials/exploit/sol.py` ← `work/materials/pwn-v11/gh-69a56364382cede9b3074e69/solve/sol.py` (`ec9c2ed78543b8b38a37a0a696723d55bb44539fac391d616026c783b4c17a70`, 2476 bytes)
  - B (6):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-69a56364382cede9b3074e69/build/Dockerfile` (`6216e9226a2204c670073f59f2966d00c4cca47a318ffbb78baa5afffcd3baa9`, 621 bytes)
    - `materials/deployment/run.sh` ← `work/materials/pwn-v11/gh-69a56364382cede9b3074e69/build/run.sh` (`c23c8b986c7c07467b3ca038b600265fe5d3c0715c941f4dbf991734710082b1`, 135 bytes)
    - `materials/deployment/solution/sol.py` ← `work/materials/pwn-v11/gh-69a56364382cede9b3074e69/build/solution/sol.py` (`ec9c2ed78543b8b38a37a0a696723d55bb44539fac391d616026c783b4c17a70`, 2476 bytes)
    - `materials/deployment/src_code/Makefile` ← `work/materials/pwn-v11/gh-69a56364382cede9b3074e69/build/src_code/Makefile` (`3a3d58262c5d0250c042960460cb17d7b7202c4624322cf3f5c33826ca0678ac`, 246 bytes)
    - `materials/deployment/src_code/src/main.c` ← `work/materials/pwn-v11/gh-69a56364382cede9b3074e69/build/src_code/src/main.c` (`df09a45c177183d1298e128ef1b8581f6aa5625a485b77c010deaf92aeaa6885`, 8541 bytes)
    - `materials/deployment/start_services.sh` ← `work/materials/pwn-v11/gh-69a56364382cede9b3074e69/build/start_services.sh` (`a85fb88f6543ffb94d2677f0870850ebbdbd4921c013bfd7dc38147807201555`, 185 bytes)

### 98. `gh-d0f6a02821b09bf650b0de62` — filelen

- Identity: welcome ctf / 2023 / Pwn
- Source: `NUSGreyhats/welcome-ctf-2023-public`; `https://github.com/NUSGreyhats/welcome-ctf-2023-public/tree/0bd49fa66c76d6948a1264ada51e81f65c818b25/challenges/pwn/filelen`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `system_libc`; `other`
- Selection reason: adds event welcome ctf; adds source NUSGreyhats/welcome-ctf-2023-public
- Material fingerprint: `da084293416084479bfa1f734ef6ef28006c519f4dd8f24dc4e9b4e38e5967e9`
- Material paths:
  - A (2):
    - `materials/attachments/chall` ← `work/materials/pwn-v11/gh-d0f6a02821b09bf650b0de62/public/chall` (`64d86584485db0534a516ef818ce0c0ecd44e95f36e40a599f3f3c4ca56981f2`, 16736 bytes)
    - `materials/attachments/chall.c` ← `work/materials/pwn-v11/gh-d0f6a02821b09bf650b0de62/public/chall.c` (`77f92190ac164b0ac4186b3b960892b096e60ff0fc2e14a1ca528fa3e4a5b973`, 1150 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/gh-d0f6a02821b09bf650b0de62/solve/solve.py` (`2fe20c65c8f5d2496cae4a21850300d956d04442478ce788cb13eae04ce1ee0c`, 214 bytes)
  - B (3):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-d0f6a02821b09bf650b0de62/build/Dockerfile` (`f15c92de4178f08549bb31dc5aa1562f58796dce4c8bbd242b3103995aac61cd`, 148 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/gh-d0f6a02821b09bf650b0de62/build/docker-compose.yml` (`d1b313c83330fdfe2dbcfdd4f6ae3e34defb810182e0e974f234ee47388a0390`, 127 bytes)
    - `materials/deployment/src/chall.c` ← `work/materials/pwn-v11/gh-d0f6a02821b09bf650b0de62/build/src/chall.c` (`77f92190ac164b0ac4186b3b960892b096e60ff0fc2e14a1ca528fa3e4a5b973`, 1150 bytes)

### 99. `gh-a118f52e8c160dc35e81533c` — My boundaries

- Identity: Hack Till Shour 2k22 CTF / 2022 / Pwn
- Source: `Shellmates/Hack-Till-Shour-2k22-CTF-challs`; `https://github.com/Shellmates/Hack-Till-Shour-2k22-CTF-challs/tree/99452a29dca1a7727549833be6eda80e9a6aab80/pwn/My_boundaries`
- Formal route: `AWPB` → `fast_track_full`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `system_libc`; `other`
- Selection reason: adds event Hack Till Shour 2k22 CTF; adds source Shellmates/Hack-Till-Shour-2k22-CTF-challs
- Material fingerprint: `1c4a639125b4e3b801bb74db9e48a439d34b4f2098008a23d7553a667ab598b4`
- Material paths:
  - A (2):
    - `materials/attachments/challenge` ← `work/materials/pwn-v11/gh-a118f52e8c160dc35e81533c/public/challenge` (`31589914214fdb6fadf6a24c22e441ab1062e26682ef2f5fabd70773384fb1ff`, 16424 bytes)
    - `materials/attachments/challenge.c` ← `work/materials/pwn-v11/gh-a118f52e8c160dc35e81533c/public/challenge.c` (`fb70eb7daa8024f2ff152a46b57c9255a1b055b3820e6ecc0635978a07ecd531`, 940 bytes)
  - W (1):
    - `materials/writeups/README.md` ← `work/materials/pwn-v11/gh-a118f52e8c160dc35e81533c/writeups/README.md` (`de6b766a8669351636a0db23d52c3f04cbc768e0d38260aae10bfeac73fa081d`, 467 bytes)
  - P (1):
    - `materials/exploit/script.py` ← `work/materials/pwn-v11/gh-a118f52e8c160dc35e81533c/solve/script.py` (`996672affd3649b0abf20fb686d6a3d235dcceeeaf048da1cda41a47cbf57e33`, 172 bytes)
  - B (5):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/gh-a118f52e8c160dc35e81533c/build/Dockerfile` (`3a1da00938884ed9c97859101ce11fe13e7eb8dbd985bc5e0184a090ff95e076`, 244 bytes)
    - `materials/deployment/challenge/entrypoint.sh` ← `work/materials/pwn-v11/gh-a118f52e8c160dc35e81533c/build/challenge/entrypoint.sh` (`1a73ad467858b60765cbeb667937565d23051fe18bec09e54dd94dc962b10cd8`, 97 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/gh-a118f52e8c160dc35e81533c/build/docker-compose.yml` (`6a43567392ebed446eabc606f318c6f1c82a4de0ac5bd5865354339cd86db300`, 339 bytes)
    - `materials/deployment/solution/script.py` ← `work/materials/pwn-v11/gh-a118f52e8c160dc35e81533c/build/solution/script.py` (`996672affd3649b0abf20fb686d6a3d235dcceeeaf048da1cda41a47cbf57e33`, 172 bytes)
    - `materials/deployment/src/challenge.c` ← `work/materials/pwn-v11/gh-a118f52e8c160dc35e81533c/build/src/challenge.c` (`fb70eb7daa8024f2ff152a46b57c9255a1b055b3820e6ecc0635978a07ecd531`, 940 bytes)

### 100. `saj-2024-pwn-free-free-free` — free_free_free

- Identity: SECCON / 2024 / Pwn
- Source: `SECCON/SECCON_Beginners_CTF_2024`; `https://github.com/sajjadium/ctf-archives/tree/main/ctfs/SECCON/2024/Quals/pwn/free_free_free`
- Formal route: `APB` → `fast_track_no_writeup`
- Build/runtime/EXP: `dockerfile_compose`; `hybrid`; `system_libc`; `heap`, `stack_rop`
- Selection reason: adds event SECCON; adds source SECCON/SECCON_Beginners_CTF_2024
- Material fingerprint: `8ec9024413c2ae24aaa9dfc3a2ac938c19da9b50d96bad4bbaa5ddb67f03b51a`
- Material paths:
  - A (2):
    - `materials/attachments/free-free_free/chall` ← `work/materials/pwn-v11/saj-2024-pwn-free-free-free/public/free-free_free/chall` (`33b66c09199959d8ee58545790bc63a9602f98050f9463e18f1ef05fe355e579`, 16656 bytes)
    - `materials/attachments/free-free_free/src/free3.c` ← `work/materials/pwn-v11/saj-2024-pwn-free-free-free/public/free-free_free/src/free3.c` (`ebb836a4d7367a2e50991d79c1b8c6205099d968d85b93b24fc2c9b48554fefc`, 2183 bytes)
  - W: absent
  - P (1):
    - `materials/exploit/solve.py` ← `work/materials/pwn-v11/saj-2024-pwn-free-free-free/solve/solve.py` (`5ecedf540a4e9a9a0940a01b32a2f90a2c1ac16a2b295470ff5e5f125f40309b`, 7976 bytes)
  - B (3):
    - `materials/deployment/Dockerfile` ← `work/materials/pwn-v11/saj-2024-pwn-free-free-free/build/Dockerfile` (`5e42f6e2c3845604f15c98cdc615764daa8865cba24fbee1d6658690152f2e17`, 343 bytes)
    - `materials/deployment/docker-compose.yml` ← `work/materials/pwn-v11/saj-2024-pwn-free-free-free/build/docker-compose.yml` (`a4e9d90df6c1ac737d632a7178f41f1c975cef5ac0c93970f862f66f1f897677`, 325 bytes)
    - `materials/deployment/src/free3.c` ← `work/materials/pwn-v11/saj-2024-pwn-free-free-free/build/src/free3.c` (`ebb836a4d7367a2e50991d79c1b8c6205099d968d85b93b24fc2c9b48554fefc`, 2183 bytes)

## Automated verification

The verifier recomputes the deterministic selection from the formal database, checks the balanced profile quotas, canonical identities, role states, unique IDs/material fingerprints, every source and dataset path, byte size, SHA-256, archive integrity, task contracts, and report coverage.

```bash
python examples/build_target/scripts/materialize_p1_control_subset.py verify
```

Static A/W/P/B evidence is inventory only; none of these tasks is reported as R3, R4, R5, or any X tier.
