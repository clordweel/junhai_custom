from junhai_custom.custom_methods.currency import generate_in_words


def validate(doc, method):
    """
    在保存和提交时强制覆盖金额大写
    """
    generate_in_words(doc, method)
