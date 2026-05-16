from constants import modes, buckets, priorities, keys
import logging

logger = logging.getLogger(__name__)


def validate_object(obj: dict) -> None:
    if 'mode' not in obj:
        logger.warning("Validation failed: mode key not present")
        return 'Mode key not present'
    if obj['mode'] not in modes:
        logger.warning(f"Validation failed: invalid mode '{obj['mode']}'")
        return 'Mode response was not valid'
    if obj['mode'] == 'task':
        for key in keys:
            if key not in obj:
                logger.warning(f"Validation failed: missing key '{key}'")
                return 'Missing one or more of the necessary keys'
        if obj['bucket'] not in buckets:
            logger.warning(f"Validation failed: invalid bucket '{obj['bucket']}'")
            return 'Bucket value was not part of the valid options'
        min_p, max_p = priorities
        if obj['priority'] > max_p or obj['priority'] < min_p:
            logger.warning(f"Validation failed: priority {obj['priority']} out of range")
            return f'Priority must be between {min_p} and {max_p}'
    else:
        if 'response' not in obj:
            logger.warning("Validation failed: response key not present")
            return 'response key not present'
    return


def validate_response(data: list) -> None:
    if not isinstance(data, list):
        logger.warning("Validation failed: response is not a list")
        return 'Response must be a list'
    for item in data:
        result = validate_object(item)
        if result:
            return result
    logger.info("Validation passed")
    return