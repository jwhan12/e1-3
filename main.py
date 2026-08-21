import json
import math
import re
import time

EPSILON = 1e-9
REPEAT_COUNT = 10
REQUIRED_JSON_SIZES = (5, 13, 25)


def print_section(number, title):
    print()
    print("#---------------------------------------")
    print(f"# [{number}] {title}")
    print("#---------------------------------------")


def normalize_label(value):
    """JSON/필터 라벨을 프로그램 내부 표준 라벨 Cross 또는 X로 바꾼다."""
    text = str(value).strip().lower()

    if text in ("+", "cross"):
        return "Cross"
    if text == "x":
        return "X"

    raise ValueError(f"지원하지 않는 라벨: {value}")


def validate_square_matrix(matrix, expected_size):
    """matrix가 expected_size x expected_size 숫자 배열인지 검사한다."""
    if not isinstance(matrix, list):
        return False, "2차원 배열(list)이 아닙니다."

    if len(matrix) != expected_size:
        return False, f"행 수가 {expected_size}가 아닙니다. (현재 {len(matrix)})"

    for row_index, row in enumerate(matrix, start=1):
        if not isinstance(row, list):
            return False, f"{row_index}번째 행이 배열(list)이 아닙니다."

        if len(row) != expected_size:
            return False, f"{row_index}번째 행의 열 수가 {expected_size}가 아닙니다. (현재 {len(row)})"

        for col_index, value in enumerate(row, start=1):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return False, f"{row_index}행 {col_index}열 값이 숫자가 아닙니다."

            if not math.isfinite(float(value)):
                return False, f"{row_index}행 {col_index}열 값이 유한한 숫자가 아닙니다."

    return True, ""


def mac(pattern, filter_matrix):
    """두 N x N 배열의 같은 위치 값을 곱해 모두 더한다."""
    total = 0.0

    for row_index in range(len(pattern)):
        for col_index in range(len(pattern[row_index])):
            total += pattern[row_index][col_index] * filter_matrix[row_index][col_index]

    return total


def decide_two_scores(score_a, score_b, label_a="A", label_b="B"):
    """epsilon 기반으로 두 점수를 비교한다."""
    if abs(score_a - score_b) < EPSILON:
        return "UNDECIDED"
    if score_a > score_b:
        return label_a
    return label_b


def measure_mac_average(pattern, filter_matrix, repeat_count=REPEAT_COUNT):
    """I/O를 제외하고 MAC 함수 호출 구간만 반복 측정해 평균 ms를 반환한다."""
    elapsed_times = []

    for _ in range(repeat_count):
        start = time.perf_counter()
        mac(pattern, filter_matrix)
        end = time.perf_counter()
        elapsed_times.append((end - start) * 1000.0)

    return sum(elapsed_times) / len(elapsed_times)


def read_matrix(name, size=3):
    """콘솔에서 size x size 숫자 배열을 입력받고 오류 시 전체 배열을 다시 받는다."""
    while True:
        print(f"{name} ({size}줄 입력, 공백 구분)")
        matrix = []
        has_error = False

        for _ in range(size):
            line = input().strip()
            parts = line.split()

            if len(parts) != size:
                has_error = True
                # 현재 입력 묶음의 나머지 줄을 강제로 받지 않고 즉시 다시 시작한다.
                break

            try:
                row = [float(value) for value in parts]
            except ValueError:
                has_error = True
                break

            matrix.append(row)

        if not has_error and len(matrix) == size:
            return matrix

        print(
            f"입력 형식 오류: 각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요."
        )
        print("처음부터 다시 입력해 주세요.")
        print()


def make_cross_pattern(size):
    """성능 측정용 N x N Cross 패턴을 만든다."""
    matrix = [[0.0 for _ in range(size)] for _ in range(size)]
    center = size // 2

    for index in range(size):
        matrix[center][index] = 1.0
        matrix[index][center] = 1.0

    return matrix


def format_score(score):
    """정수에 가까운 값은 1자리 소수, 나머지는 읽기 쉬운 유효숫자로 표시한다."""
    if abs(score - round(score)) < EPSILON:
        return f"{score:.1f}"
    return f"{score:.16g}"


def print_performance_table(sizes):
    print("크기       평균 시간(ms)    연산 횟수")
    print("-------------------------------------")

    for size in sizes:
        pattern = make_cross_pattern(size)
        filter_matrix = make_cross_pattern(size)
        average_ms = measure_mac_average(pattern, filter_matrix, REPEAT_COUNT)

        print(
            f"{size:>2}×{size:<2}      {average_ms:>10.6f}      {size * size:>6}"
        )


def parse_pattern_size(case_id):
    match = re.fullmatch(r"size_(\d+)_(\d+)", str(case_id))
    if match is None:
        raise ValueError(
            "패턴 키 형식이 size_{{N}}_{{idx}} 규칙과 다릅니다."
        )
    return int(match.group(1))


def load_json_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        raise ValueError(f"data.json 파일을 찾을 수 없습니다: {file_path}")
    except json.JSONDecodeError as error:
        raise ValueError(
            f"data.json JSON 문법 오류: line {error.lineno}, column {error.colno}"
        )

    if not isinstance(data, dict):
        raise ValueError("data.json 최상위 구조는 객체(dict)여야 합니다.")

    if "filters" not in data or not isinstance(data["filters"], dict):
        raise ValueError("data.json에 filters 객체가 없습니다.")

    if "patterns" not in data or not isinstance(data["patterns"], dict):
        raise ValueError("data.json에 patterns 객체가 없습니다.")

    return data


def prepare_filters(raw_filters):
    """
    size_5/13/25 필터를 읽고 filter key(cross/x)를
    표준 라벨(Cross/X)로 정규화한다.
    """
    prepared = {}
    errors = {}

    for size in REQUIRED_JSON_SIZES:
        size_key = f"size_{size}"
        group = raw_filters.get(size_key)

        if not isinstance(group, dict):
            errors[size] = f"{size_key} 필터 객체가 없습니다."
            continue

        normalized_group = {}
        group_error = None

        for raw_label, matrix in group.items():
            try:
                normalized_label = normalize_label(raw_label)
            except ValueError as error:
                group_error = str(error)
                break

            valid, reason = validate_square_matrix(matrix, size)
            if not valid:
                group_error = f"{normalized_label} 필터 크기/값 오류: {reason}"
                break

            if normalized_label in normalized_group:
                group_error = f"정규화 후 필터 라벨이 중복됩니다: {normalized_label}"
                break

            normalized_group[normalized_label] = matrix

        if group_error is not None:
            errors[size] = group_error
            continue

        missing_labels = [
            label for label in ("Cross", "X") if label not in normalized_group
        ]
        if missing_labels:
            errors[size] = f"필수 필터 라벨이 없습니다: {', '.join(missing_labels)}"
            continue

        prepared[size] = normalized_group

    return prepared, errors


def analyze_json_patterns(patterns, filters, filter_errors):
    results = []

    for case_id, case_data in patterns.items():
        result = {
            "case_id": case_id,
            "status": "FAIL",
            "reason": "",
            "expected": None,
            "prediction": None,
            "cross_score": None,
            "x_score": None,
        }

        try:
            size = parse_pattern_size(case_id)
        except ValueError as error:
            result["reason"] = str(error)
            results.append(result)
            continue

        if not isinstance(case_data, dict):
            result["reason"] = "패턴 항목이 객체(dict)가 아닙니다."
            results.append(result)
            continue

        if "input" not in case_data or "expected" not in case_data:
            result["reason"] = "input 또는 expected 필드가 없습니다."
            results.append(result)
            continue

        try:
            expected = normalize_label(case_data["expected"])
        except ValueError as error:
            result["reason"] = f"expected 라벨 오류: {error}"
            results.append(result)
            continue

        result["expected"] = expected

        valid, reason = validate_square_matrix(case_data["input"], size)
        if not valid:
            result["reason"] = f"패턴 크기/값 오류: {reason}"
            results.append(result)
            continue

        if size not in filters:
            result["reason"] = filter_errors.get(
                size, f"size_{size}에 대응하는 필터가 없습니다."
            )
            results.append(result)
            continue

        filter_group = filters[size]
        pattern = case_data["input"]

        cross_score = mac(pattern, filter_group["Cross"])
        x_score = mac(pattern, filter_group["X"])
        prediction = decide_two_scores(cross_score, x_score, "Cross", "X")

        result["cross_score"] = cross_score
        result["x_score"] = x_score
        result["prediction"] = prediction

        if prediction == expected:
            result["status"] = "PASS"
            result["reason"] = "판정과 expected가 일치합니다."
        elif prediction == "UNDECIDED":
            result["reason"] = (
                f"두 점수 차이가 epsilon({EPSILON})보다 작아 UNDECIDED로 판정되었습니다."
            )
        else:
            result["reason"] = f"판정 {prediction}와 expected {expected}가 다릅니다."

        results.append(result)

    return results


def run_user_input_mode():
    print_section(1, "필터 입력")
    filter_a = read_matrix("필터 A", 3)
    print("✓ 필터 A 저장 완료")
    print()

    filter_b = read_matrix("필터 B", 3)
    print("✓ 필터 B 저장 완료")

    print_section(2, "패턴 입력")
    pattern = read_matrix("패턴", 3)
    print("✓ 패턴 저장 완료")

    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)
    decision = decide_two_scores(score_a, score_b, "A", "B")
    average_ms = measure_mac_average(pattern, filter_a, REPEAT_COUNT)

    print_section(3, "MAC 결과")
    print(f"A 점수: {format_score(score_a)}")
    print(f"B 점수: {format_score(score_b)}")
    print(
        f"연산 시간(평균/{REPEAT_COUNT}회): {average_ms:.6f} ms"
    )

    if decision == "UNDECIDED":
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"판정: {decision}")

    print_section(4, f"성능 분석 (평균/{REPEAT_COUNT}회)")
    print_performance_table((3,))


def run_json_mode(file_path):
    try:
        data = load_json_file(file_path)
    except ValueError as error:
        print()
        print(f"[오류] {error}")
        return

    filters, filter_errors = prepare_filters(data["filters"])

    print_section(1, "필터 로드")
    for size in REQUIRED_JSON_SIZES:
        if size in filters:
            print(f"✓ size_{size} 필터 로드 완료 (Cross, X)")
        else:
            print(f"✗ size_{size} 필터 로드 실패: {filter_errors.get(size, '알 수 없는 오류')}")

    print_section(2, "패턴 분석 (라벨 정규화 적용)")
    results = analyze_json_patterns(data["patterns"], filters, filter_errors)

    for result in results:
        print(f'--- {result["case_id"]} ---')

        if result["cross_score"] is not None:
            print(f'Cross 점수: {format_score(result["cross_score"])}')
            print(f'X 점수: {format_score(result["x_score"])}')
            print(
                f'판정: {result["prediction"]} | expected: {result["expected"]} | {result["status"]}'
            )
        else:
            expected_text = result["expected"] or "UNKNOWN"
            print(
                f"판정: UNAVAILABLE | expected: {expected_text} | FAIL"
            )

        if result["status"] == "FAIL":
            print(f'사유: {result["reason"]}')

        print()

    print_section(3, f"성능 분석 (평균/{REPEAT_COUNT}회)")
    print_performance_table((3, 5, 13, 25))

    total = len(results)
    passed = sum(1 for result in results if result["status"] == "PASS")
    failed = total - passed

    print_section(4, "결과 요약")
    print(f"전체 테스트 수: {total}")
    print(f"통과 수: {passed}")
    print(f"실패 수: {failed}")

    if failed:
        print("실패 케이스:")
        for result in results:
            if result["status"] == "FAIL":
                print(f'- {result["case_id"]}: {result["reason"]}')
    else:
        print("실패 케이스: 없음")


def read_mode():
    while True:
        print()
        print("[모드 선택]")
        print("1. 사용자 입력 (3x3)")
        print("2. data.json 분석")
        choice = input("선택: ").strip()

        if choice in ("1", "2"):
            return choice

        print("입력 오류: 1 또는 2를 입력해 주세요.")


def main():
    print("=== Mini NPU Simulator ===")

    mode = read_mode()

    if mode == "1":
        run_user_input_mode()
    else:
        run_json_mode("./data.json")


if __name__ == "__main__":
    main()