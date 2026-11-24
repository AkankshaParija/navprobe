# Failure gallery

Tasks that the most models answered wrongly (base tasks only).


## F1 count doors

- **F1-e0002** (plan, 14x14): correct **3**; vllm_OpenGVLab_InternVL3_5-8B: 1, vllm_Qwen_Qwen2.5-VL-3B-Instruct: 2, vllm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ: 2, vllm_Qwen_Qwen2.5-VL-7B-Instruct: 2, vllm_Qwen_Qwen3-VL-32B-Instruct-FP8: 2, vllm_Qwen_Qwen3-VL-4B-Instruct: 2, vllm_Qwen_Qwen3-VL-8B-Instruct: 2; evidence `{"closed_doorways": 1, "open_doorways": 3}`
- **F1-e0005** (plan, 14x14): correct **3**; vllm_OpenGVLab_InternVL3_5-8B: 1, vllm_Qwen_Qwen2.5-VL-3B-Instruct: 2, vllm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ: 2, vllm_Qwen_Qwen2.5-VL-7B-Instruct: 2, vllm_Qwen_Qwen3-VL-32B-Instruct-FP8: 2, vllm_Qwen_Qwen3-VL-4B-Instruct: 2, vllm_Qwen_Qwen3-VL-8B-Instruct: 2; evidence `{"closed_doorways": 1, "open_doorways": 3}`
- **F1-e0008** (ros, 14x14): correct **3**; vllm_OpenGVLab_InternVL3_5-8B: 1, vllm_Qwen_Qwen2.5-VL-3B-Instruct: 2, vllm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ: 2, vllm_Qwen_Qwen2.5-VL-7B-Instruct: 2, vllm_Qwen_Qwen3-VL-32B-Instruct-FP8: 2, vllm_Qwen_Qwen3-VL-4B-Instruct: 2, vllm_Qwen_Qwen3-VL-8B-Instruct: 2; evidence `{"closed_doorways": 0, "open_doorways": 3}`

## F2 left/right

- **F2-e0000** (plan, 14x14): correct **left**; vllm_OpenGVLab_InternVL3_5-8B: right, vllm_Qwen_Qwen2.5-VL-3B-Instruct: right, vllm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ: right, vllm_Qwen_Qwen2.5-VL-7B-Instruct: right, vllm_Qwen_Qwen3-VL-32B-Instruct-FP8: right, vllm_Qwen_Qwen3-VL-4B-Instruct: right, vllm_Qwen_Qwen3-VL-8B-Instruct: right; evidence `{"angle_from_heading_deg": 60.3}`
- **F2-e0002** (plan, 14x14): correct **left**; vllm_OpenGVLab_InternVL3_5-8B: right, vllm_Qwen_Qwen2.5-VL-3B-Instruct: right, vllm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ: right, vllm_Qwen_Qwen2.5-VL-7B-Instruct: right, vllm_Qwen_Qwen3-VL-32B-Instruct-FP8: right, vllm_Qwen_Qwen3-VL-4B-Instruct: right, vllm_Qwen_Qwen3-VL-8B-Instruct: right; evidence `{"angle_from_heading_deg": 126.9}`
- **F2-e0003** (plan, 14x14): correct **right**; vllm_OpenGVLab_InternVL3_5-8B: left, vllm_Qwen_Qwen2.5-VL-3B-Instruct: left, vllm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ: left, vllm_Qwen_Qwen2.5-VL-7B-Instruct: left, vllm_Qwen_Qwen3-VL-32B-Instruct-FP8: left, vllm_Qwen_Qwen3-VL-4B-Instruct: left, vllm_Qwen_Qwen3-VL-8B-Instruct: left; evidence `{"angle_from_heading_deg": 82.9}`

## F3 reachable?

- **F3-e0026** (plan, 14x14): correct **yes**; vllm_OpenGVLab_InternVL3_5-8B: None, vllm_Qwen_Qwen2.5-VL-3B-Instruct: no, vllm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ: no, vllm_Qwen_Qwen2.5-VL-7B-Instruct: no, vllm_Qwen_Qwen3-VL-32B-Instruct-FP8: no, vllm_Qwen_Qwen3-VL-4B-Instruct: no, vllm_Qwen_Qwen3-VL-8B-Instruct: no; evidence `{"reachable": true}`
- **F3-e0002** (plan, 14x14): correct **yes**; vllm_OpenGVLab_InternVL3_5-8B: None, vllm_Qwen_Qwen2.5-VL-3B-Instruct: no, vllm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ: no, vllm_Qwen_Qwen2.5-VL-7B-Instruct: no, vllm_Qwen_Qwen3-VL-32B-Instruct-FP8: no, vllm_Qwen_Qwen3-VL-4B-Instruct: no, vllm_Qwen_Qwen3-VL-8B-Instruct: yes; evidence `{"reachable": true}`
- **F3-e0028** (ros, 14x14): correct **yes**; vllm_OpenGVLab_InternVL3_5-8B: no, vllm_Qwen_Qwen2.5-VL-3B-Instruct: no, vllm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ: no, vllm_Qwen_Qwen2.5-VL-7B-Instruct: yes, vllm_Qwen_Qwen3-VL-32B-Instruct-FP8: no, vllm_Qwen_Qwen3-VL-4B-Instruct: no, vllm_Qwen_Qwen3-VL-8B-Instruct: no; evidence `{"reachable": true}`

## F4 fits?

- **F4-s0078** (ros, 20x20): correct **yes**; vllm_OpenGVLab_InternVL3_5-8B: None, vllm_Qwen_Qwen2.5-VL-3B-Instruct: no, vllm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ: no, vllm_Qwen_Qwen2.5-VL-7B-Instruct: no, vllm_Qwen_Qwen3-VL-32B-Instruct-FP8: no, vllm_Qwen_Qwen3-VL-4B-Instruct: no, vllm_Qwen_Qwen3-VL-8B-Instruct: no; evidence `{"fits": true, "robot_size_cells": 2}`
- **F4-e0020** (ros, 14x14): correct **yes**; vllm_OpenGVLab_InternVL3_5-8B: yes, vllm_Qwen_Qwen2.5-VL-3B-Instruct: no, vllm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ: no, vllm_Qwen_Qwen2.5-VL-7B-Instruct: no, vllm_Qwen_Qwen3-VL-32B-Instruct-FP8: no, vllm_Qwen_Qwen3-VL-4B-Instruct: no, vllm_Qwen_Qwen3-VL-8B-Instruct: no; evidence `{"fits": true, "robot_size_cells": 2}`
- **F4-e0040** (plan, 14x14): correct **yes**; vllm_OpenGVLab_InternVL3_5-8B: yes, vllm_Qwen_Qwen2.5-VL-3B-Instruct: no, vllm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ: no, vllm_Qwen_Qwen2.5-VL-7B-Instruct: no, vllm_Qwen_Qwen3-VL-32B-Instruct-FP8: no, vllm_Qwen_Qwen3-VL-4B-Instruct: no, vllm_Qwen_Qwen3-VL-8B-Instruct: no; evidence `{"fits": true, "robot_size_cells": 2}`

## F5 nearest by path

- **F5-e0008** (ros, 14x14): correct **C**; vllm_OpenGVLab_InternVL3_5-8B: None, vllm_Qwen_Qwen2.5-VL-3B-Instruct: B, vllm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ: B, vllm_Qwen_Qwen2.5-VL-7B-Instruct: B, vllm_Qwen_Qwen3-VL-32B-Instruct-FP8: B, vllm_Qwen_Qwen3-VL-4B-Instruct: B, vllm_Qwen_Qwen3-VL-8B-Instruct: B; evidence `{"euclid": {"A": 6.71, "B": 2.24, "C": 7.62}, "path_len": {"A": 23, "B": 29, "C": 16}, "straight_line_nearest": "B", "trap": true}`
- **F5-e0014** (plan, 14x14): correct **C**; vllm_OpenGVLab_InternVL3_5-8B: None, vllm_Qwen_Qwen2.5-VL-3B-Instruct: B, vllm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ: B, vllm_Qwen_Qwen2.5-VL-7B-Instruct: B, vllm_Qwen_Qwen3-VL-32B-Instruct-FP8: B, vllm_Qwen_Qwen3-VL-4B-Instruct: B, vllm_Qwen_Qwen3-VL-8B-Instruct: B; evidence `{"euclid": {"A": 7.81, "B": 2.0, "C": 5.0}, "path_len": {"A": 11, "B": 10, "C": 5}, "straight_line_nearest": "B", "trap": true}`
- **F5-e0020** (ros, 14x14): correct **C**; vllm_OpenGVLab_InternVL3_5-8B: None, vllm_Qwen_Qwen2.5-VL-3B-Instruct: B, vllm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ: B, vllm_Qwen_Qwen2.5-VL-7B-Instruct: B, vllm_Qwen_Qwen3-VL-32B-Instruct-FP8: B, vllm_Qwen_Qwen3-VL-4B-Instruct: A, vllm_Qwen_Qwen3-VL-8B-Instruct: B; evidence `{"euclid": {"A": 7.07, "B": 8.54, "C": 8.06}, "path_len": {"A": 28, "B": 15, "C": 11}, "straight_line_nearest": "A", "trap": true}`

## F6 line of sight

- **F6-e0001** (plan, 14x14): correct **blocked**; vllm_OpenGVLab_InternVL3_5-8B: visible, vllm_Qwen_Qwen2.5-VL-3B-Instruct: blocked, vllm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ: visible, vllm_Qwen_Qwen2.5-VL-7B-Instruct: visible, vllm_Qwen_Qwen3-VL-32B-Instruct-FP8: blocked, vllm_Qwen_Qwen3-VL-4B-Instruct: visible, vllm_Qwen_Qwen3-VL-8B-Instruct: visible; evidence `{"distance_cells": 11.18}`
- **F6-e0003** (plan, 14x14): correct **blocked**; vllm_OpenGVLab_InternVL3_5-8B: visible, vllm_Qwen_Qwen2.5-VL-3B-Instruct: blocked, vllm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ: visible, vllm_Qwen_Qwen2.5-VL-7B-Instruct: visible, vllm_Qwen_Qwen3-VL-32B-Instruct-FP8: blocked, vllm_Qwen_Qwen3-VL-4B-Instruct: visible, vllm_Qwen_Qwen3-VL-8B-Instruct: visible; evidence `{"distance_cells": 11.18}`
- **F6-e0005** (ros, 14x14): correct **blocked**; vllm_OpenGVLab_InternVL3_5-8B: visible, vllm_Qwen_Qwen2.5-VL-3B-Instruct: blocked, vllm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ: visible, vllm_Qwen_Qwen2.5-VL-7B-Instruct: visible, vllm_Qwen_Qwen3-VL-32B-Instruct-FP8: blocked, vllm_Qwen_Qwen3-VL-4B-Instruct: visible, vllm_Qwen_Qwen3-VL-8B-Instruct: visible; evidence `{"distance_cells": 5.83}`
