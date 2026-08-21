import json
import math
import time

EPSILON = 1e-9
REPEAT_COUNT = 10
JSON_SIZES = (5, 13, 25)


def print_section(number, title):
    """출력 내용을 구분하기 위한 제목 영역을 출력한다."""
    print()
    print("#---------------------------------------")
    print(f"# [{number}] {title}")
    print("#---------------------------------------")


def normalize_label(value):
    """입력 라벨을 프로그램 내부 표준 라벨로 바꾼다."""
    label = str(value).strip().lower()

    # 같은 의미로 사용되는 라벨을 하나의 표준 라벨로 통일한다.
    if label in ("+", "cross"):
        return "Cross"
    if label == "x":
        return "X"

    raise ValueError(f"지원하지 않는 라벨: {value}")


def validate_matrix(matrix, size):
    """size x size 숫자 배열이면 None, 아니면 오류 사유를 반환한다."""
    # 먼저 전체 행의 개수가 요구한 크기와 같은지 확인한다.
    if not isinstance(matrix, list) or len(matrix) != size:
        return f"행 수가 {size}가 아닙니다."

    # 각 행의 열 개수와 내부 값의 형식을 차례로 검사한다.
    for row_number, row in enumerate(matrix, start=1):
        if not isinstance(row, list) or len(row) != size:
            return f"{row_number}번째 행의 열 수가 {size}가 아닙니다."

        # bool, 문자열, NaN, Infinity처럼 MAC에 사용할 수 없는 값을 거부한다.
        for value in row:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                return f"{row_number}번째 행에 숫자가 아닌 값이 있습니다."

    return None


def mac(pattern, filter_matrix):
    """두 N x N 배열의 같은 위치 값을 곱해 모두 더한다."""
    total = 0.0

    # 두 행렬의 같은 위치에 있는 값을 하나씩 꺼내 곱한다.
    for row in range(len(pattern)):
        for col in range(len(pattern[row])):
            pattern_value = pattern[row][col]
            filter_value = filter_matrix[row][col]

            product = pattern_value * filter_value
            total += product

    return total


def decide(score_a, score_b, label_a="A", label_b="B"):
    """epsilon 기준으로 두 점수를 비교한다."""
    score_difference = abs(score_a - score_b)

    # 두 점수의 차이가 매우 작으면 부동소수점 오차로 보고 동점 처리한다.
    if score_difference < EPSILON:
        return "UNDECIDED"

    # 동점이 아니면 더 높은 점수를 얻은 라벨을 반환한다.
    if score_a > score_b:
        return label_a

    return label_b


def average_mac_time(pattern, filter_matrix, repeat_count=REPEAT_COUNT):
    """MAC 함수 호출 시간만 반복 측정해 평균 ms를 반환한다."""
    total_ms = 0.0

    # 한 번의 측정값에 치우치지 않도록 MAC 연산을 여러 번 측정한다.
    for _ in range(repeat_count):
        start = time.perf_counter()
        mac(pattern, filter_matrix)
        end = time.perf_counter()

        elapsed_seconds = end - start
        elapsed_ms = elapsed_seconds * 1000
        total_ms += elapsed_ms

    average_ms = total_ms / repeat_count
    return average_ms


def read_matrix(name, size=3):
    """콘솔에서 size x size 숫자 배열을 입력받는다."""
    # 올바른 행렬이 입력될 때까지 전체 입력 과정을 반복한다.
    while True:
        print(f"{name} ({size}줄 입력, 공백 구분)")
        matrix = []

        try:
            # 한 줄씩 읽어 숫자 목록으로 변환한다.
            for _ in range(size):
                values = input().split()

                if len(values) != size:
                    raise ValueError

                row = [float(value) for value in values]
                matrix.append(row)

            return matrix

        # 열 개수가 다르거나 숫자로 변환할 수 없으면 처음부터 다시 입력받는다.
        except ValueError:
            print(
                f"입력 형식 오류: 각 줄에 {size}개의 숫자를 "
                "공백으로 구분해 입력하세요."
            )
            print("처음부터 다시 입력해 주세요.\n")


def print_performance_table(sizes):
    """각 행렬 크기의 평균 MAC 시간과 연산 횟수를 출력한다."""
    print("크기(N×N)    평균 시간(ms)    연산 횟수(N²)")
    print("------------------------------------------")

    # 전달받은 모든 크기에 대해 같은 방식으로 성능을 측정한다.
    for size in sizes:
        matrix = [[1.0] * size for _ in range(size)]
        average_ms = average_mac_time(matrix, matrix)
        operation_count = size * size

        print(f"{size}×{size}    {average_ms:.6f}    {operation_count}")


def parse_pattern_size(case_id):
    """size_{N}_{idx} 형식의 키에서 N을 꺼낸다."""
    parts = str(case_id).split("_")

    # 키가 size, 행렬 크기, 순번의 세 부분으로 구성됐는지 확인한다.
    if (
        len(parts) != 3
        or parts[0] != "size"
        or not parts[1].isdigit()
        or not parts[2].isdigit()
    ):
        raise ValueError("패턴 키 형식이 size_{N}_{idx} 규칙과 다릅니다.")

    size = int(parts[1])
    return size


def load_json(file_path):
    """JSON 파일을 읽고 필수 최상위 구조를 검증한다."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        raise ValueError(f"data.json 파일을 찾을 수 없습니다: {file_path}")
    except json.JSONDecodeError as error:
        raise ValueError(
            f"data.json JSON 문법 오류: "
            f"line {error.lineno}, column {error.colno}"
        )

    # 이후 로직에서 사용할 수 있도록 최상위 객체와 필수 항목을 확인한다.
    if not isinstance(data, dict):
        raise ValueError("data.json 최상위 구조는 객체(dict)여야 합니다.")

    if not isinstance(data.get("filters"), dict):
        raise ValueError("data.json에 filters 객체가 없습니다.")

    if not isinstance(data.get("patterns"), dict):
        raise ValueError("data.json에 patterns 객체가 없습니다.")

    return data


def prepare_filters(raw_filters):
    """필터를 검증하고 라벨을 Cross/X로 정규화한다."""
    filters = {}
    errors = {}

    # 과제에서 요구하는 각 크기의 필터를 독립적으로 준비한다.
    for size in JSON_SIZES:
        size_key = f"size_{size}"
        group = raw_filters.get(size_key)

        if not isinstance(group, dict):
            errors[size] = f"{size_key} 필터 객체가 없습니다."
            continue

        normalized = {}
        error_message = None

        # 필터 라벨을 통일하고 각 필터 행렬의 크기와 값을 검사한다.
        for raw_label, matrix in group.items():
            try:
                label = normalize_label(raw_label)
            except ValueError as error:
                error_message = str(error)
                break

            matrix_error = validate_matrix(matrix, size)

            if matrix_error:
                error_message = f"{label} 필터 오류: {matrix_error}"
                break

            normalized[label] = matrix

        # Cross와 X 필터 중 하나라도 없으면 해당 크기의 필터를 사용할 수 없다.
        if error_message is None and "Cross" not in normalized:
            error_message = "Cross 필터가 없습니다."

        if error_message is None and "X" not in normalized:
            error_message = "X 필터가 없습니다."

        if error_message:
            errors[size] = error_message
        else:
            filters[size] = normalized

    return filters, errors


def failed_result(case_id, reason, expected=None):
    """분석할 수 없는 케이스의 공통 실패 결과를 만든다."""
    result = {
        "case_id": case_id,
        "status": "FAIL",
        "reason": reason,
        "expected": expected,
        "prediction": None,
        "cross_score": None,
        "x_score": None,
    }

    return result


def analyze_case(case_id, case_data, filters, filter_errors):
    """JSON 패턴 한 개를 검증하고 판정한다."""
    # 케이스 ID에서 사용할 필터의 크기를 확인한다.
    try:
        size = parse_pattern_size(case_id)
    except ValueError as error:
        return failed_result(case_id, str(error))

    # 케이스가 input과 expected를 담을 수 있는 객체인지 검사한다.
    if not isinstance(case_data, dict):
        return failed_result(case_id, "패턴 항목이 객체(dict)가 아닙니다.")

    if "input" not in case_data or "expected" not in case_data:
        return failed_result(case_id, "input 또는 expected 필드가 없습니다.")

    # expected 값을 실제 판정 결과와 비교할 표준 라벨로 바꾼다.
    try:
        expected = normalize_label(case_data["expected"])
    except ValueError as error:
        return failed_result(case_id, f"expected 라벨 오류: {error}")

    pattern = case_data["input"]

    # 패턴의 크기나 값이 잘못되면 MAC 연산을 수행하지 않는다.
    matrix_error = validate_matrix(pattern, size)

    if matrix_error:
        return failed_result(case_id, f"패턴 오류: {matrix_error}", expected)

    # 패턴 크기에 맞는 필터가 준비되지 않았다면 해당 케이스만 실패 처리한다.
    if size not in filters:
        default_reason = f"size_{size}에 대응하는 필터가 없습니다."
        reason = filter_errors.get(size, default_reason)
        return failed_result(case_id, reason, expected)

    filter_group = filters[size]
    cross_filter = filter_group["Cross"]
    x_filter = filter_group["X"]

    cross_score = mac(pattern, cross_filter)
    x_score = mac(pattern, x_filter)
    prediction = decide(cross_score, x_score, "Cross", "X")

    # 계산한 판정과 expected 라벨을 비교해 최종 상태를 정한다.
    if prediction == expected:
        status = "PASS"
        reason = ""
    elif prediction == "UNDECIDED":
        status = "FAIL"
        reason = (
            f"두 점수 차이가 epsilon({EPSILON})보다 작아 "
            "UNDECIDED입니다."
        )
    else:
        status = "FAIL"
        reason = f"판정 {prediction}와 expected {expected}가 다릅니다."

    result = {
        "case_id": case_id,
        "status": status,
        "reason": reason,
        "expected": expected,
        "prediction": prediction,
        "cross_score": cross_score,
        "x_score": x_score,
    }

    return result


def print_case_result(result):
    """패턴 한 건의 분석 결과를 출력한다."""
    case_id = result["case_id"]
    status = result["status"]
    prediction = result["prediction"]
    expected = result["expected"]

    print(f"--- {case_id} ---")

    # 계산하지 못한 케이스와 정상 계산된 케이스의 출력 형식을 구분한다.
    if prediction is None:
        expected_text = expected or "UNKNOWN"
        print(f"판정: UNAVAILABLE | expected: {expected_text} | FAIL")
    else:
        cross_score = result["cross_score"]
        x_score = result["x_score"]

        print(f"Cross 점수: {cross_score:.10g}")
        print(f"X 점수: {x_score:.10g}")
        print(f"판정: {prediction} | expected: {expected} | {status}")

    # 실패한 경우 사용자가 원인을 확인할 수 있도록 사유도 출력한다.
    if status == "FAIL":
        reason = result["reason"]
        print(f"사유: {reason}")

    print()


def run_user_input_mode():
    """사용자에게 3x3 필터와 패턴을 입력받아 분석한다."""
    print_section(1, "필터 입력")

    filter_a = read_matrix("필터 A")
    print("✓ 필터 A 저장 완료\n")

    filter_b = read_matrix("필터 B")
    print("✓ 필터 B 저장 완료")

    print_section(2, "패턴 입력")

    pattern = read_matrix("패턴")
    print("✓ 패턴 저장 완료")

    # 입력 패턴과 두 필터의 점수를 각각 계산한다.
    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)
    decision = decide(score_a, score_b)
    average_ms = average_mac_time(pattern, filter_a)

    print_section(3, "MAC 결과")
    print(f"A 점수: {score_a:.10g}")
    print(f"B 점수: {score_b:.10g}")
    print(f"연산 시간(평균/{REPEAT_COUNT}회): {average_ms:.6f} ms")

    # 동점 여부에 따라 판정 문구를 다르게 출력한다.
    if decision == "UNDECIDED":
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"판정: {decision}")

    print_section(4, f"성능 분석 (평균/{REPEAT_COUNT}회)")
    print_performance_table((3,))


def run_json_mode(file_path):
    """data.json의 필터와 패턴을 읽어 전체 케이스를 분석한다."""
    try:
        data = load_json(file_path)
    except ValueError as error:
        print(f"\n[오류] {error}")
        return

    raw_filters = data["filters"]
    patterns = data["patterns"]
    filters, filter_errors = prepare_filters(raw_filters)

    print_section(1, "필터 로드")

    # 크기별 필터가 정상적으로 준비됐는지 사용자에게 보여준다.
    for size in JSON_SIZES:
        if size in filters:
            print(f"✓ size_{size} 필터 로드 완료 (Cross, X)")
        else:
            error_message = filter_errors[size]
            print(f"✗ size_{size} 필터 로드 실패: {error_message}")

    print_section(2, "패턴 분석 (라벨 정규화 적용)")
    results = []

    # 한 케이스의 오류가 다른 케이스를 막지 않도록 개별적으로 분석한다.
    for case_id, case_data in patterns.items():
        result = analyze_case(case_id, case_data, filters, filter_errors)
        results.append(result)
        print_case_result(result)

    print_section(3, f"성능 분석 (평균/{REPEAT_COUNT}회)")
    print_performance_table((3, 5, 13, 25))

    # 결과 목록을 순회하며 통과한 케이스의 수를 계산한다.
    passed = 0

    for result in results:
        if result["status"] == "PASS":
            passed += 1

    total = len(results)
    failed = total - passed

    print_section(4, "결과 요약")
    print(f"전체 테스트 수: {total}")
    print(f"통과 수: {passed}")
    print(f"실패 수: {failed}")

    # 실패가 없다면 상세 목록 없이 요약 출력을 마친다.
    if failed == 0:
        print("실패 케이스: 없음")
        return

    print("실패 케이스:")

    # 실패한 케이스만 골라 원인과 함께 다시 보여준다.
    for result in results:
        if result["status"] == "FAIL":
            case_id = result["case_id"]
            reason = result["reason"]
            print(f"- {case_id}: {reason}")


def read_mode():
    """사용자가 올바른 실행 모드를 선택할 때까지 입력받는다."""
    while True:
        print("\n[모드 선택]")
        print("1. 사용자 입력 (3x3)")
        print("2. data.json 분석")

        choice = input("선택: ").strip()

        if choice in ("1", "2"):
            return choice

        print("입력 오류: 1 또는 2를 입력해 주세요.")


def main():
    """프로그램을 시작하고 선택한 모드를 실행한다."""
    print("=== Mini NPU Simulator ===")

    mode = read_mode()

    # 사용자가 선택한 모드에 따라 입력 분석 또는 JSON 분석을 실행한다.
    if mode == "1":
        run_user_input_mode()
    else:
        run_json_mode("./data.json")


if __name__ == "__main__":
    main()
