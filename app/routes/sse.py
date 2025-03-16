from flask import Blueprint, request, Response, current_app, stream_with_context, jsonify
from app.llm.llm_client import LLMClient
from app.utils.db_utils import generate_context_for_llm
import json
import time

sse_bp = Blueprint('sse', __name__, url_prefix='/sse')

@sse_bp.route('/models', methods=['GET'])
def get_available_models():
    """
    Get a list of available LLM models.
    
    Returns:
        JSON response with available models and the default model.
    """
    models = current_app.config.get('LLM_MODELS', {})
    default_model = current_app.config.get('DEFAULT_LLM_MODEL', 'gpt-3.5-turbo')
    
    # Flatten the model list for easier frontend consumption
    flat_models = []
    for provider, provider_models in models.items():
        for model in provider_models:
            flat_models.append({
                'id': model,
                'name': model,
                'provider': provider
            })
    
    return jsonify({
        'models': flat_models,
        'default_model': default_model
    })

@sse_bp.route('/llm', methods=['POST'])
def stream_llm_response():
    """
    Stream LLM responses with database context using SSE.
    
    Expected JSON payload:
    {
        "prompt": "User's question about the database",
        "tables": ["optional", "list", "of", "tables", "to", "focus", "on"],
        "model": "optional model name (default will be used if not specified)"
    }
    """
    try:
        data = request.json
        if not data or 'prompt' not in data:
            return Response(
                _format_sse_message({'error': 'Prompt is required'}),
                status=400,
                content_type='text/event-stream'
            )
        
        prompt = data['prompt']
        tables = data.get('tables', None)
        model_name = data.get('model', None)  # Get the requested model name
        
        # Generate context about the database
        context = generate_context_for_llm(prompt, tables)
        
        # Create the LLM client with optional model specification
        llm_client = LLMClient(model=model_name)
        
        # Log which model is being used
        current_app.logger.info(f"Using LLM model: {llm_client.model_name}")
        
        @stream_with_context
        def generate():
            """Generate SSE events for streaming LLM responses."""
            # Send initial event with model info
            yield _format_sse_message({
                'status': 'started',
                'model': llm_client.model_name
            })
            
            try:
                # Stream the response from the LLM
                for chunk in llm_client.generate_completion(prompt, context, streaming=True):
                    yield _format_sse_message({'chunk': chunk})
                    time.sleep(0.01)  # Small delay to avoid overwhelming the client
                
                # Send completion event
                yield _format_sse_message({'status': 'completed'})
            except Exception as e:
                current_app.logger.error(f"Error in LLM streaming: {str(e)}")
                yield _format_sse_message({'error': str(e)})
            
            # End SSE connection
            yield _format_sse_message({'status': 'closed'}, event='close')
        
        return Response(
            generate(),
            content_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'  # Disable buffering for nginx
            }
        )
        
    except Exception as e:
        current_app.logger.error(f"Error setting up LLM streaming: {str(e)}")
        return Response(
            _format_sse_message({'error': str(e)}),
            content_type='text/event-stream'
        )

def _format_sse_message(data, event='message'):
    """
    Format a message for SSE.
    
    Args:
        data: The data to send
        event: The event type (default: 'message')
        
    Returns:
        Formatted SSE message
    """
    json_data = json.dumps(data)
    return f"event: {event}\ndata: {json_data}\n\n" 