from datetime import datetime, timedelta
import time
import logging

def wait_for_run_to_complete(run_id, client, thread_id, sleep_interval=5, timeout=120):
    '''
    Wait for the run to complete and prints the elapsed time.
    '''
    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=timeout)
    while datetime.now() < end_time:
        try:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run.status == "completed" and run.completed_at:
                
                ai_elapsed_time = run.completed_at - run.created_at
                

                # Format the elapsed time as hours, minutes, seconds
                formatted_time = time.strftime("%H:%M:%S", time.gmtime(ai_elapsed_time))
                # formatted_time = str(ai_elapsed_time)  # timedelta auto-formats as HH:MM:SS
                
                print(f"Run completed in {datetime.now() - start_time}")
                print(f"Run completed at gpt level in {formatted_time}")
                # logging.info(f"Run completed in {formatted_time}")
                
                # === retrieve message === 
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                last_message = messages.data[0].content[0].text.value
                print(f"Assistant Response: {last_message}")
                break
        except Exception as e:
            print(f"Error: {e}")
            break
        logging.info(f"Waiting for run to complete...")
        time.sleep(sleep_interval)
