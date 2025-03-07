from PIL import Image

INDENT_ROUNDING = 10
SERIES_INDENTS = "    "
    
def index_list(list: list, ids: list[int]):
    return [list[i - 1] for i in ids]

def select_data_by_ids(data, ids):
    return { k: index_list(v, ids) for k, v in data.items() }

def split_data_by_rank(data, rank_type="page_num"):
    splits = []
    if len(data[rank_type]) == 0:
        return splits
    
    max_rank = max(data[rank_type])
    for rank in range(1, max_rank+1):
        ids = [i for i in range(len(data[rank_type])) if data[rank_type][i] == rank]
        # print(rank_type, rank, ids)
        data_split = select_data_by_ids(data, ids)
        splits.append(data_split)
    return splits
    
def filter_meta_data(data: dict):
    return {k:v[1:] for k, v in data.items()}

def indent_multiline(s: str):
    return "\n".join([ SERIES_INDENTS + i for i in s.split("\n")])

def to_roman(num, lower=False):
    if num < 0:
        raise ValueError("Roman numerals don’t support negative numbers")
    
    # Roman numeral symbols and their values, in descending order
    roman_values = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I")
    ]
    
    if num == 0:
        return ""  # Or "N" for "nulla" if preferred
    
    result = ""
    for value, symbol in roman_values:
        while num >= value:
            result += symbol
            num -= value
    if lower:
        result = result.lower()
    return result

def upscale_to_300_dpi(img, target_dpi=300):
    
    # Get current DPI (if available), default to 72 if not specified
    try:
        current_dpi = img.info['dpi'][0]  # Assumes square DPI
    except KeyError:
        current_dpi = 72
    
    # Calculate scaling factor
    scale_factor = target_dpi / current_dpi
    
    # Get current dimensions
    width, height = img.size
    
    # Calculate new dimensions
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    
    # Resize the image with high-quality resampling
    resized_img = img.resize((new_width, new_height), Image.LANCZOS)
    
    # Set the new DPI metadata (optional, mainly for printing)
    resized_img.info['dpi'] = (target_dpi, target_dpi)
    
    return resized_img


alphabet_lower = [chr(i) for i in range(97, 123)]
alphabet_upper = [chr(i) for i in range(65, 91)]
numerals = [str(i) for i in range(1, 100)]
roman_numerals_upper = [to_roman(i, lower=False) for i in range(1, 100)]
roman_numerals_lower = [to_roman(i, lower=True) for i in range(1, 100)]

alphabet_lower_rank = {v: i for i, v in enumerate(alphabet_lower)}
alphabet_upper_rank = {v: i for i, v in enumerate(alphabet_upper)}
numerals_rank = {v: i for i, v in enumerate(numerals)}
roman_numerals_lower_rank = {v: i for i, v in enumerate(roman_numerals_lower)}
roman_numerals_upper_rank = {v: i for i, v in enumerate(roman_numerals_upper)}


pattern_map = {
    r"^\((\d+)\).*": (numerals_rank, numerals),
    r"^\(([xiv]+)\).*": (roman_numerals_lower_rank, roman_numerals_lower),
    r"^\(([XIV]+)\).*": (roman_numerals_upper_rank, roman_numerals_upper),
    r"^\(([a-z])\).*": (alphabet_lower_rank, alphabet_lower),
    r"^\(([A-Z])\).*": (alphabet_upper_rank, alphabet_upper),
    # r"^(.*)": get_zero_rank, # Default case
}

error_correction_map = {
    "(©)": "(c)",
}