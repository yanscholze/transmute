"""Schema fechado e validação local independente do fornecedor de IA."""
import json
import math


def schema(source_ids, targets):
    return {"type": "object", "additionalProperties": False, "properties": {"suggestions": {"type": "array", "items": {"type": "object", "additionalProperties": False,
            "properties": {"source_column": {"type": "string", "enum": source_ids}, "target_column": {"type": "string", "enum": targets}, "confidence": {"type": "number", "minimum": 0, "maximum": 1}, "reason": {"type": "string"}},
            "required": ["source_column", "target_column", "confidence", "reason"]}}}, "required": ["suggestions"]}


def parse(text, source_ids, targets):
    if not isinstance(text, str) or len(text) > 100000:
        raise ValueError("Resposta de IA excessiva ou de tipo inválido.")
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("JSON com chave duplicada.")
            result[key] = value
        return result
    data = json.loads(text, object_pairs_hook=no_duplicates)
    if not isinstance(data, dict) or set(data) != {"suggestions"} or not isinstance(data["suggestions"], list) or len(data["suggestions"]) > len(source_ids):
        raise ValueError("Schema de resposta de IA inválido.")
    seen_source, seen_target = set(), set()
    for item in data["suggestions"]:
        if not isinstance(item, dict) or set(item) != {"source_column", "target_column", "confidence", "reason"}:
            raise ValueError("Sugestão de IA contém campos inválidos.")
        source, target, confidence = item["source_column"], item["target_column"], item["confidence"]
        if not isinstance(source, str) or source not in source_ids or not isinstance(target, str) or target not in targets:
            raise ValueError("IA referenciou coluna inexistente.")
        if type(confidence) not in (int, float) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError("Confiança da IA inválida.")
        if not isinstance(item["reason"], str) or len(item["reason"]) > 500:
            raise ValueError("Justificativa de IA inválida.")
        if source in seen_source or target in seen_target:
            raise ValueError("IA produziu mapeamentos conflitantes.")
        seen_source.add(source)
        seen_target.add(target)
    return data["suggestions"]
