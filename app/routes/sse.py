from flask import Blueprint, request, Response, current_app, stream_with_context
from app.llm.llm_client import LLMClient
from app.utils.db_utils import generate_context_for_llm
import json
import time

sse_bp = Blueprint('sse', __name__, url_prefix='/sse')

@sse_bp.route('/llm', methods=['POST'])
def stream_llm_response():
    """
    Stream LLM responses with database context using SSE.
    
    Expected JSON payload:
    {
        "prompt": "User's question about the database",
        "tables": ["optional", "list", "of", "tables", "to", "focus", "on"]
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
        
        # Generate context about the database
        context = generate_context_for_llm(prompt, tables)
        
        # Create the LLM client (will use environment vars or app config)
        llm_client = LLMClient()
        
        @stream_with_context
        def generate():
            """Generate SSE events for streaming LLM responses."""
            # Send initial event
            yield _format_sse_message({'status': 'started'})
            
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