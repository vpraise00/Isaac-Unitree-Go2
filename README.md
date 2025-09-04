# Isaac-Unitree-Go2 (Windows 11, Isaac Sim 5.0, Isaac Lab 2.2)

이 저장소는 go2_omniverse(구 Isaac Sim/Orbit 기반) 프로젝트를 Windows 11 + Isaac Sim 5.0 + Isaac Lab 2.2 환경으로 포팅/재구성한 버전입니다. ROS 2/Humble 및 실제 로봇 연동은 제외하고, 레포 내부에서 제공하는 창고/오피스류 환경을 불러와 GO2를 조작/학습하는 워크플로우를 제공합니다.

- OS: Windows 11
- Simulator: Isaac Sim 5.0 Standalone (GUI)
- Learning: Isaac Lab 2.2 (manager-based tasks + RSL-RL wrappers)
- ROS 2: 사용하지 않음 (코드/구조는 시뮬 전용)

주요 차이점
- 구 레포(go2_omniverse)의 Orbit/ROS2 구성 대신, 본 레포는 Lab 2.2 + 5.0 네임스페이스(isaacsim.*)를 사용합니다.
- 창고/오피스 환경은 Isaac Lab 자산 또는 로컬 USD로 로드하며, Windows 경로 규칙과 5.0의 렌더러/입력/On-Demand 규칙을 따릅니다.

포팅 체크리스트(진행 상황)
- 구조/런타임
  - [x] Windows 배치 실행기(`tools/isaac_unitree_go2.bat`) 추가 (Isaac Sim 5.0 호출 → Python 러너)
  - [x] 통합 러너(`tools/isaac_unitree_go2.py`): --run_cfg, --env, --task, --algorithm/--checkpoint, --headless, --render_mode
  - [x] 5.0 입력/렌더/OmniGraph On-Demand 호환 (carb.input.is_key_down / RayTracedLighting / carb.settings)
  - [x] 확장(`exts/my.company.go2lab`): omni.usd 컨텍스트 + settings 기반 On-Demand, GO2 스폰
  - [x] 레코더(`isaacsim.replicator.writers`) 호환 및 입력 이벤트 갱신
- 환경/자산
  - [x] 환경 레지스트리(`env/registry.yaml`): warehouse 등 이름별 매핑
  - [ ] office 등 추가 환경 매핑(Isaac Lab 자산 경로 확인 후 반영)
  - [x] USD 경로 유틸(로컬/URL/isaaclab:// 스킴) 및 로드 정책 정비
- 조작/실행
  - [x] Teleop(키보드) — GO2 항상 스폰, 초기 포즈 적용, 입력 생략 모드(SKIP_INPUT)
  - [x] Dataset Recorder — 카메라/채널 선택, 프레임 메타(JSONL)
  - [x] 빈 스테이지 실행 옵션 및 안전한 SimulationApp 라이프사이클
- 학습/추론
  - [x] RL 로코모션 러너(`locomotion_runner.py`): Isaac-Velocity-Flat-Unitree-Go2-v0 실행, RSL-RL 체크포인트 로드
  - [x] 레포 내 RL env/cfg 네임스페이스(`src/go2lab/rl/...`) 정리
  - [ ] Rough 변형/다중 환경/속도 향상(headless batch) 프리셋 추가

디렉터리 개요(포팅 후)
- tools/
  - isaac_unitree_go2.bat — Windows용 Isaac Sim 5.0 실행 래퍼
  - isaac_unitree_go2.py — 통합 러너(teleop/train/test/locomotion RL)
- src/go2lab/
  - sim/scripts/ — run_sim, teleop_keyboard, dataset_recorder, train/test/locomotion_runner
  - sim/util/ — kit(OmniGraph on-demand), usd_path 등
  - rl/ — go2_ctrl_cfg/go2_ctrl + envs/go2_env (Lab 2.2용)
  - world.py, env_registry.py — 환경 로더/매핑
- env/registry.yaml — 환경 이름 → USD 스펙 매핑(isaaclab:// 스킴 지원)
- exts/my.company.go2lab — Isaac Sim 확장(시작 시 환경/GO2 준비)

go2_omniverse 대비 매핑
- Orbit 기반 스크립트(main.py, omniverse_sim.py 등) → tools/runner + src/go2lab/sim/scripts/* 로 대체
- ROS2 관련(ws, msg, nodes) → 포함하지 않음(시뮬 전용)
- terrain/omnigraph 커스텀 요소 → Lab 2.2 매니저/태스크로 점진 전환(필요 시 포팅)

## 사전 준비
- Windows 11
- Isaac Sim 5.0 Standalone 설치(경로 예시):
  `D:\My_Project\Sim\isaac-sim-standalone-5.0.0-windows-x86_64\isaac-sim.bat`
- Visual Studio Code (권장)
- ROS 2 불필요

Isaac Sim 설치 경로가 다르면 `.vscode/tasks.json`의 배치 파일 경로를 수정하세요.

## 빠른 시작 (VS Code 태스크)
VS Code 메뉴에서 Terminal > Run Task를 열고 아래 태스크를 실행하세요.

1) Run Isaac Sim (script-runner)
- GUI 실행 → Warehouse 스테이지 로드 또는 생성 → 최소 240 프레임 업데이트 후 종료.
  - 성능 우선 렌더링: 배치/러너에 `--render_mode performance` 추가 (기본 RTX 실시간)

2) Run Isaac Sim (extension)
- `my.company.go2lab` 확장을 활성화해 GUI 실행.
- Warehouse 생성/로드, GO2 스폰, OmniGraph Compute Mode=On Demand 적용.

3) Record Dataset (script)
- GUI 실행, GO2 스폰, 카메라 설정, BasicWriter로 출력(`output/<timestamp>/`).
  - `--render_mode performance`로 프레임 드랍을 줄일 수 있습니다.
- 실행 중 키보드로 조작하면서 동시에 기록 가능.

참고: 에디터에서 `pxr`, `carb`, `isaacsim.*` 임포트가 해석되지 않는 것은 정상입니다(Isaac Sim 런타임에서 제공). 항상 배치/태스크를 통해 실행하세요.

## 조작법 (키보드)
- 이동: W/S(전/후), A/D(좌/우)
- 회전: 방향키 좌/우
- 브레이크: Space
- 부스트: Left Shift

## 출력/데이터셋
- 결과는 `output/YYYYMMDD-HHMMSS/` 아래에 저장됩니다.
- 선택 채널 이미지(RGB/Depth/Semantic/Instance)와 `meta.jsonl`(프레임별 메타)가 포함됩니다.

## 설정 (환경변수)
실행 전 환경변수로 동작을 조정할 수 있습니다.
- 시뮬레이션
  - `SIM_MIN_STEPS` (기본 240)
  - `WAREHOUSE_USD` (기본: Nucleus 설정을 사용해 `omniverse://.../NVIDIA/Isaac/IsaacLab/Environments/Simple_Warehouse/warehouse.usd`로 구성). 다음 형식을 지원: 절대경로, 저장소상 상대경로, 옴니버스 URL(`omniverse://`, `omni://`) 및 `http(s)://`). 로컬 경로를 지정했는데 파일이 없으면 에러로 종료합니다(자동 생성하지 않음).
  - `SIM_LOG_LEVEL` (예: INFO/DEBUG)
- 키보드 조작
  - `TELEOP_MAX_VX`, `TELEOP_MAX_VY`, `TELEOP_MAX_WZ`
  - `TELEOP_ACCEL`, `TELEOP_DAMP`
- GO2 자산
  - `GO2_USD` (GO2 USD 경로). 절대/상대, Isaac 토큰, 옴니버스 URL 모두 지원. 미설정이고 `sim/usd/go2.usd`가 없으면 플레이스홀더가 스폰됩니다.
- 레코더
  - `REC_FPS`(기본 20), `REC_WIDTH`/`REC_HEIGHT`
  - `REC_ATTACH_TO_GO2` (1: GO2 장착, 0: 월드 고정 카메라)
  - `REC_CHANNELS` (쉼표 구분: `rgb,depth,semantic,instance`)
  - `REC_DURATION_SEC` (기본 30)

## 폴더 구조 개요
- src/go2lab/sim/scripts/run_sim.py — GUI 실행, Warehouse 오픈/생성, 프레임 스텝, On Demand 적용.
- src/go2lab/sim/scripts/warehouse_gen.py — 절차적 Warehouse 생성, 저장 옵션.
- src/go2lab/sim/scripts/spawn_go2.py — GO2 스폰/리셋 + 간단 베이스 컨트롤러.
- src/go2lab/sim/scripts/teleop_keyboard.py — `carb.input` 기반 키보드 조작.
- src/go2lab/sim/scripts/dataset_recorder.py — `isaacsim.replicator.writers` BasicWriter로 기록.
- `exts/my.company.go2lab/` — Isaac Sim 확장(시작 시 스테이지/환경/GO2 준비, On Demand 적용).
- `configs/go2_task_config.yaml` — Isaac Lab 2.2 태스크 스켈레톤.
- `src/go2lab/core/managers.py` — manager 기반 테스트 더블(Action/Sensor/Reward) 구현.
- `src/go2lab/lab/envs/go2_warehouse_env.py` — Isaac Sim에서 동작하는 GO2 warehouse 테스트 더블 환경.
- src/go2lab/lab/scripts/preview_task.py — YAML 로드 후 랜덤 정책으로 짧은 롤아웃 실행.
- `docs/CONTEXT.md` — 전체 흐름/가드레일/DoD.
- `docs/MAPPINGS_45_to_50.md` — 4.5/1.x → 5.0/2.2 네임스페이스 매핑.

## API 가드레일 (중요)
- 사용: `isaacsim.core.api`, `isaacsim.core.nodes`, `isaacsim.sensors.*`, `isaacsim.replicator.*`, `isaacsim.storage.native`, `isaacsim.core.cloner`.
- 금지: `omni.isaac.*`, `omni.replicator.isaac` (구형 네임스페이스 금지).
- OmniGraph: Compute Mode를 On Demand로 설정해 "Physics OnSimulationStep" 경고가 발생하지 않도록 합니다.
- 본 단계에서는 ROS 2/브리지 사용 금지.

## Definition of Done (수동 체크)
1) GUI가 뜨고 Warehouse가 보이며 최소 240 프레임 업데이트.
2) GO2 스폰 및 키보드 조작(전/후/좌/우/회전/정지)이 부드럽게 동작(클램핑/브레이크 포함).
3) 데이터셋 기록 시 `output/` 하위에 선택 채널 이미지와 프레임별 JSONL 메타 저장.
4) On Demand 설정으로 OnSimulationStep 경고 0건.
5) Lab 2.2 테스트 더블(프리뷰)이 YAML을 로드하고 관측/보상/액션을 포함한 짧은 롤아웃을 수행.

## 트러블슈팅
- Isaac Sim 설치 경로가 다르면 `.vscode/tasks.json`을 수정하세요.
- `pxr`, `carb` 임포트 경고는 에디터에서만 보이는 현상입니다. 태스크로 실행하면 런타임 환경에서 해결됩니다.
- GO2 USD를 보유했다면 `GO2_USD` 환경변수로 지정하세요. 없다면 플레이스홀더 캡슐이 생성됩니다.

## 다음 단계
- 확장(UI)에 Teleop/Recorder 시작/정지 토글 버튼 추가.
- 테스트 더블을 Isaac Lab 2.2 runtime의 manager_based Task로 점진적 교체(입출력 계약 유지).
- SensorManager: 실제 센서/피직스와 연동해 속도/자세 추정 정교화.
- RewardManager: 과업별 shaping/penalty/termination 속성 추가.

## Manager 기반 테스트 더블(관측/보상)
- 관측(observations):
  - base_lin_vel (xyz), base_ang_vel (yaw만), base_height, imu_quat(간이 yaw 기반), up_dot(수직성), yaw, pos
- 보상(rewards):
  - survive_bonus(+), forward_progress(+x 속도), smoothness(Δaction L2 페널티), lateral_pen(|y 속도| 페널티), upright(up_dot 가중)

## Lab Preview 실행
- VS Code > Terminal > Run Task > "Lab Preview (manager-based test-double)"
- 또는 yaml 없이도 기본값으로 60스텝 랜덤 정책 롤아웃이 수행됩니다.

## 실행 가이드 (Step-by-Step)
아래 순서대로 실행하면 환경이 정상 동작하는지 빠르게 확인할 수 있습니다.

1) 경로/사전 설정 확인
- Isaac Sim 배치 경로: `.vscode/tasks.json`의 `isaac-sim.bat` 경로가 실제 설치 위치와 일치하는지 확인
- (선택) Isaac Lab 2.2 경로: `configs/lab2_config.json`에서 `lab_repo`가 로컬 Isaac Lab 레포 루트를 가리키는지 확인

2) Warehouse + GO2 기본 확인
- 태스크: "Run Isaac Sim (script-runner)" 실행
- 기대 결과: GUI가 열리고 Warehouse가 로드/생성됨 → 카메라가 장면을 비추며 내부적으로 최소 240프레임 진행 후 자동 종료
- 참고 로그: "On Demand compute" 적용, warehouse USD 경로, stage open/create 메시지

3) 확장으로 구동 확인(동일 동작을 Ext로)
- 태스크: "Run Isaac Sim (extension)" 실행
- 기대 결과: GUI가 열리고 확장이 스테이지/환경/GO2를 준비, On Demand 적용

4) Manager 기반 프리뷰 확인
- 태스크: "Lab Preview (manager-based test-double)" 실행
- 기대 결과: 터미널 로그에 reset obs 요약, rollout finished(steps, return) 출력 후 종료
- 파라미터 변경: `configs/go2_task_config.yaml`에서 physics_hz/control_hz/max_episode_length 수정 가능

5) 공식 Isaac Lab 2.2 태스크 실행
- `configs/lab2_config.json`에서 `lab_repo` 경로가 올바른지 확인
- 태스크: "Run Isaac Lab 2.2 task module" 실행
- 기대 결과: Isaac Lab 모듈 표준 출력(학습/롤아웃 로깅) 확인, 실패 시 모듈/경로 오류 메시지 확인

6) 커스텀 창고 태스크 실행
- 태스크: "Run Custom Warehouse Task" 실행
- 기대 결과: 로컬 warehouse 환경에서 짧은 롤아웃 수행, steps/return 로그 표시
- 커스터마이즈: `src/go2lab/lab/scripts/run_custom_task.py`에서 보상/정책/종료 로직 확장

### 태스크별 파라미터 변경 팁
- 전역 파라미터는 주로 `.vscode/tasks.json` 혹은 각 스크립트의 인자/설정 파일에서 제어
- 예) 프리뷰 주기: `configs/go2_task_config.yaml`의 `control_hz`
- 예) 커스텀 태스크: `run_custom_task.py` 인자 `--max-steps`, `--control-hz`, `--headless`

### Windows 명령줄로 직접 실행 (선택)
VS Code 태스크 대신 명령줄에서 직접 실행할 수도 있습니다(레포 루트에서 실행 권장).

프리뷰 실행:
```cmd
"D:\My_Project\Sim\isaac-sim-standalone-5.0.0-windows-x86_64\isaac-sim.bat" --enable isaacsim.core.nodes --exec "%CD%\lab\scripts\preview_task.py"
```

공식 Lab 2.2 모듈 실행(모듈명 교체 가능):
```cmd
"D:\My_Project\Sim\isaac-sim-standalone-5.0.0-windows-x86_64\isaac-sim.bat" --enable isaacsim.core.nodes --exec "%CD%\lab\scripts\run_lab2_task.py" -- --task-module omni.isaac.lab_tasks.manager_based.locomotion.run
```

커스텀 창고 태스크 실행(옵션 인자 예시):
```cmd
"D:\My_Project\Sim\isaac-sim-standalone-5.0.0-windows-x86_64\isaac-sim.bat" --enable isaacsim.core.nodes --exec "%CD%\lab\scripts\run_custom_task.py" -- --max-steps 300 --control-hz 30
```

헤드리스(디스플레이 없이)로 실행하려면 `--headless` 플래그를 추가하세요(지원 스크립트 한정).

### 흔한 문제 해결
- pxr/carb/isaacsim 임포트 경고: 에디터에서만 보이는 정상 현상입니다. 반드시 Isaac Sim 배치로 실행하세요.
- 모듈 실행 실패(공식 Lab 2.2): `lab_repo` 경로가 올바른지, 모듈 경로가 정확한지 확인하세요.
- 카메라/데이터셋 출력 없음: `REC_*` 환경변수(프레임률/해상도/채널)를 확인하고, writer enable 로그를 확인하세요.
- OnSimulationStep 경고: OmniGraph Compute Mode가 On Demand로 설정되는지 로그를 확인하세요.

## Isaac Lab 2.2 manager_based 태스크 실행(공식 모듈)
- `configs/lab2_config.json`의 `lab_repo`를 로컬 Isaac Lab 2.2 체크아웃 경로로 설정하세요.
- VS Code 태스크: "Run Isaac Lab 2.2 task module" 실행.
  - 기본으로 `omni.isaac.lab_tasks.manager_based.locomotion.run` 모듈을 실행합니다.
  - 다른 모듈 실행이 필요하면 태스크의 인자를 변경하거나 아래 명령을 참고하세요.

## 커스텀 창고 태스크 실행(레포 내 테스트 더블)
- VS Code 태스크: "Run Custom Warehouse Task" 실행.
- `src/go2lab/lab/scripts/run_custom_task.py`가 로컬 `Go2WarehouseEnv`와 Manager 테스트 더블을 사용해 짧은 롤아웃을 수행합니다.
- 이 스크립트를 복사/수정해 나만의 보상/정책/커리큘럼을 구현할 수 있습니다.

참고: 레포는 단일 루트 구조(src/go2lab, exts/, docs/)로 정리되어 있습니다.

## 통합 실행 러너 (CLI)
다음 배치/파이썬 러너로 환경과 실행 구성을 한 번에 지정할 수 있습니다.

- 배치 파일: `tools/isaac_unitree_go2.bat`
- 파이썬 러너: `tools/isaac_unitree_go2.py`

예시:
```cmd
tools\isaac_unitree_go2.bat --run_cfg teleoperation --env warehouse_multiple_shelves --task go2-locomotion
```

렌더링 모드 지정:
```cmd
tools\isaac_unitree_go2.bat --run_cfg teleoperation --env warehouse --render_mode performance
```
지원값: performance | quality | pathtraced (pathtraced는 매우 느림)

지원 run_cfg:
- `teleoperation` (키보드 조작)
- `dataset_record` (레코더)
- `lab_preview` (테스트 더블 프리뷰)
- `lab_task_module` (Isaac Lab 모듈 실행, `--task-module` 필요)
- `custom_task` (레포 내 커스텀 태스크)
- `script_runner` (기본 run_sim 실행)

환경 지정(`--env`):
- 이름 또는 직접 경로/URL 사용 가능. 이름은 `env/registry.yaml`에서 매핑됩니다.
- `isaaclab://<rel>` 스킴 지원 (Nucleus 설정 기반 IsaacLab 자산 URL로 변환).

## 리팩토링 메모: 디렉터리 정리 및 소스 패키지화
- 핵심 코드는 `src/go2lab` 패키지로 이동/집중되었습니다.
- 모든 모듈은 `src/go2lab` 아래의 단일 소스 오브 트루스를 사용합니다.
- 확장과 통합 러너는 가능하면 `go2lab.*` 네임스페이스를 우선 사용합니다.
- 새로 추가된 설정 파일은 `configs/` 디렉터리에 위치합니다.

## 로드맵 & 체크리스트 (요약)

현재 상태(TL;DR)
- [x] Isaac Lab 스타일의 USD 경로 규칙 통일(로컬/URL/Nucleus), 기본 Warehouse는 Isaac Lab Simple Warehouse
- [x] Isaac Sim 5.0 네임스페이스(isaacsim.*) 고정, OmniGraph On-Demand 적용 유틸
- [x] Teleop, Dataset Recorder(isaacsim.replicator.writers), GO2 스폰(미보유 시 플레이스홀더)
- [x] Manager 기반 테스트더블(Action/Sensor/Reward) + 간단 환경(lab/envs)
- [x] 환경 레지스트리(env/registry.yaml, isaaclab:// 스킴)
- [x] 통합 러너(tools/isaac_unitree_go2.py) + Windows 배치 + VS Code 태스크
- [x] 소스 패키지 `src/go2lab` 정리, sim/lab는 얇은 호환 레이어로 단순화
- [ ] RL/IL 학습/추론 엔트리포인트, 멀티에이전트 태스크 본격화, 레지스트리 확장 등

1) 레포지토리/런타임
- [x] src/go2lab 패키지화 및 경로 주입(러너/확장)
- [x] sim/, lab/ 모듈은 go2lab 재사용으로 중복 제거
- [x] configs/ 디렉터리 신설(lab2_config.json 이동)
- [x] 빈 디렉터리 정리 및 불필요 파일 정돈(스크립트는 src/go2lab/* 로 통일)
- [ ] 간단한 패키징/의존성 명세(문서화 중심; Isaac 런타임 의존 알림)

2) USD/자산/월드
- [x] USD 경로 유틸(normalize/classify/resolve, isaaclab_asset_path)
- [x] Warehouse 오픈 정책(로컬 미존재 기본 에러; 자동 생성 금지)
- [x] 절차적 Warehouse 생성기(옵션 저장)
- [ ] env/registry.yaml 엔트리 확장(예: warehouse_small, multiple_shelves, full_warehouse 등)
- [ ] 로컬 USD 유효성 점검/가이드 강화(로그 메시지/문서)

3) 시뮬레이션/실행 플로우
- [x] Teleop(키보드), Recorder(채널 선택), 기본 run_sim
- [x] Extension(my.company.go2lab)에서 Warehouse/GO2 준비 및 On-Demand 적용
- [x] 통합 러너: --run_cfg, --env, --task, --agents, --checkpoint, --headless 지원
- [x] VS Code 태스크: GO2 Runner 프리셋(teleoperation/dataset/lab preview/custom/policy)
- [ ] 추가 태스크 프리셋(headless/multi-agent/학습/평가) 및 변수화

4) Lab 스타일 환경/매니저
- [x] Action/Sensor/Reward Manager(테스트더블)
- [x] Go2WarehouseEnv(리셋/스텝/보상 등 기본 루프)
- [ ] 태스크 스펙 확장(로코모션/로코매니퓰레이션 구분, 관측/행동 스펙 상세화)
- [ ] 에피소드 종료/보상 구성 강화 및 설정화(YAML/JSON)

5) RL/IL 통합(계획)
- [ ] RL 트레이닝 엔트리포인트(go2lab 환경 어댑터, Gym/Env API 브리지)
- [ ] IL 파이프라인(데이터셋 포맷/로더, 행동클로닝/DAgger 등)
- [ ] 체크포인트 포맷/스키마 통일(torchscript 또는 state_dict + 메타)
- [ ] 평가/추론 스크립트 표준화(--checkpoint, --episodes, --seed)
- [ ] 로깅/메트릭(TensorBoard/W&B), 시드 고정/재현성
- [ ] GPU/CPU 선택, headless 고속 스텝, 벤치마킹 가이드

6) 멀티에이전트(계획)
- [ ] --agents=multi 동작의 관측/행동/보상 매니저 확장
- [ ] 멀티에이전트 샘플 태스크(예: 협업 운반/회피)
- [ ] 중앙/분산 정책 실행/학습 스위치 및 샘플 설정

7) 데이터/리플리케이터
- [x] isaacsim.replicator.writers 기반 BasicWriter 연동
- [ ] 어노테이션 스키마 문서화 및 샘플 변환 스크립트(IL용)
- [ ] 추가 채널/센서 옵션(법선/포인트클라우드 등) 및 성능 가이드

8) 테스트/품질
- [ ] 경로 유틸/레지스트리 단위테스트(로컬/URL/isaaclab 스킴)
- [ ] 간단 스모크 스크립트(cmd): stage 열기 → 몇 프레임 업데이트 → 종료
- [ ] (선택) CI 워크플로우 초안(정적 검사/문서 링크 체크)

9) 문서/예제
- [x] README: 통합 러너 사용법, 리팩토링 메모 반영
- [ ] 튜토리얼: 단일 에이전트 → 멀티에이전트로 확장하는 방법
- [ ] 트러블슈팅 확장(Nucleus, 파일권한/네트워크, 그래픽 드라이버)