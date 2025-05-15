from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from markupsafe import Markup
from . import visual
from ...models import db, Dataset, Visualisation, Share, User # db import might be redundant if not used directly
from .forms import GenerateVisualisationForm, ShareVisualisationForm
# from ...services.claude_client import ClaudeClient # No longer importing the class directly
from ...services import claude_service # Import the initialized instance
from ... import cache, socketio 
import traceback
import re
import os 
import pandas as pd 
import json 
import anthropic # For specific API error handling


# claude_client = ClaudeClient() # REMOVE THIS LINE - use claude_service instance

# Helper function to clean/prepare HTML template from Claude (consolidated logic)
# This function can be moved to a utils file if it grows or is used elsewhere
def prepare_dashboard_template_html(html_content):
    """
    Clean and validate the dashboard HTML TEMPLATE to ensure it's suitable for iframe display
    and later data injection.
    """
    if not html_content:
        current_app.logger.warning("Empty HTML content provided to prepare_dashboard_template_html")
        return "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Error</title></head><body><h2>No dashboard content template available.</h2></body></html>"

    # Ensure the HTML starts with doctype
    if not html_content.strip().lower().startswith("<!doctype html"):
        html_content = "<!DOCTYPE html>\n" + html_content
    
    # Basic HTML structure checks
    if "<html" not in html_content.lower():
        html_content = html_content.replace("<!DOCTYPE html>", "<!DOCTYPE html>\n<html lang='en'>", 1)
        if "</html>" not in html_content.lower(): html_content += "\n</html>"
    
    head_start_idx = html_content.lower().find("<head>")
    head_end_idx = html_content.lower().find("</head>")

    if head_start_idx == -1: 
        html_tag_end = html_content.lower().find("<html>")
        insert_pos = html_tag_end + len("<html>") if html_tag_end != -1 else len("<!DOCTYPE html>")
        html_content = html_content[:insert_pos] + "\n<head><meta charset=\"UTF-8\"><title>Dashboard</title></head>\n" + html_content[insert_pos:]
        head_start_idx = html_content.lower().find("<head>") 
        head_end_idx = html_content.lower().find("</head>")

    if head_start_idx != -1 and "<meta charset" not in html_content[head_start_idx:head_end_idx if head_end_idx!=-1 else len(html_content)].lower():
        html_content = html_content[:head_start_idx+6] + "<meta charset=\"UTF-8\">\n" + html_content[head_start_idx+6:]
        head_end_idx = html_content.lower().find("</head>") 

    if "<body" not in html_content.lower():
        if head_end_idx != -1:
            html_content = html_content[:head_end_idx+7] + "\n<body>\n</body>" + html_content[head_end_idx+7:]
        elif "</html>" in html_content.lower():
            idx = html_content.lower().find("</html>")
            html_content = html_content[:idx] + "\n<body>\n</body>\n" + html_content[idx:]
        else:
            html_content += "\n<body>\n</body>"

    current_head_content = html_content[head_start_idx:head_end_idx if head_end_idx!=-1 else len(html_content)]

    if head_start_idx != -1 and '<meta name="viewport"' not in current_head_content.lower():
        viewport_meta = '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">\n'
        html_content = html_content[:head_start_idx+6] + viewport_meta + html_content[head_start_idx+6:]
        head_end_idx = html_content.lower().find("</head>")

    if head_start_idx != -1 and '<meta http-equiv="Content-Security-Policy"' not in current_head_content:
        csp_tag = '<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\' \'unsafe-inline\' https://cdn.jsdelivr.net https://d3js.org; style-src \'self\' \'unsafe-inline\' https://cdn.jsdelivr.net; img-src \'self\' data: blob:; connect-src \'self\'; font-src \'self\' https://cdn.jsdelivr.net;">\n'
        html_content = html_content[:head_start_idx+6] + csp_tag + html_content[head_start_idx+6:]
        head_end_idx = html_content.lower().find("</head>")
    
    if head_end_idx != -1: 
        responsive_css_script = """
<style>
    html, body { width: 100% !important; height: 100% !important; margin: 0 !important; padding: 0 !important; overflow-x: hidden !important; box-sizing: border-box !important; }
    *, *:before, *:after { box-sizing: inherit !important; }
    #dashboard-content, #root, #app, main, .main, .dashboard, .dashboard-main,
    .container, .container-fluid, .row, .grid, div[class*="container"], section, article, .card, .panel, .box {
        width: 100% !important; max-width: 100% !important; margin-left: auto !important; margin-right: auto !important;
    }
    canvas, svg, .chart, div[class*="chart"] { width: 100% !important; max-width: 100% !important; height: auto !important; }
    img, table { max-width: 100% !important; height: auto !important; }
</style>
"""
        html_content = html_content[:head_end_idx] + responsive_css_script + html_content[head_end_idx:]

    if "console.error('Dashboard error:'" not in html_content:
        error_handling_script = """
<script>
    window.addEventListener('error', function(event) {
        console.error('Dashboard error:', event.message, 'at', event.filename, ':', event.lineno);
        var errorDisplay = document.getElementById('dynadashInternalErrorDisplay');
        if (!errorDisplay && document.body) {
            errorDisplay = document.createElement('div');
            errorDisplay.id = 'dynadashInternalErrorDisplay';
            errorDisplay.style.cssText = 'position:fixed;top:5px;left:5px;right:5px;padding:10px;background:rgba(220,50,50,0.9);color:white;border-radius:4px;z-index:20000;font-family:sans-serif;font-size:14px;';
            document.body.insertBefore(errorDisplay, document.body.firstChild);
        }
        if(errorDisplay) errorDisplay.textContent = 'Dashboard Error: ' + event.message + ' (in ' + (event.filename || 'inline script') + ':' + event.lineno + ')';
    });
    document.addEventListener('DOMContentLoaded', function() {
        if (typeof window.dynadashData === 'undefined' || window.dynadashData === null || (Array.isArray(window.dynadashData) && window.dynadashData.length === 0)) {
            console.warn('window.dynadashData is not defined or is empty. Dashboard might not render correctly.');
            var dataWarningDiv = document.getElementById('dynadashDataWarningDisplay');
            if(!dataWarningDiv && document.body) {
                dataWarningDiv = document.createElement('div');
                dataWarningDiv.id = 'dynadashDataWarningDisplay';
                dataWarningDiv.style.cssText = 'padding:10px;background:rgba(255,220,50,0.8);color:black;text-align:center;font-family:sans-serif;font-size:14px;';
                dataWarningDiv.textContent = 'Notice: Data for this dashboard (window.dynadashData) was not loaded or is empty. Visualizations may not appear as expected.';
                document.body.insertBefore(dataWarningDiv, document.body.firstChild);
            }
        }
        setTimeout(function() {
            if (typeof Chart !== 'undefined' && typeof window.dynadashData !== 'undefined') {
                var canvases = document.querySelectorAll('canvas');
                canvases.forEach(function(canvas) {
                    try {
                        var chartInstance = Chart.getChart(canvas); 
                        if (chartInstance) { chartInstance.update('none'); } 
                    } catch(e) { console.warn('Could not update chart on canvas ' + (canvas.id || '(no id)') + ':', e); }
                });
            }
        }, 1200);
    });
</script>
"""
        body_end_idx = html_content.lower().rfind('</body>')
        if body_end_idx != -1:
            html_content = html_content[:body_end_idx] + error_handling_script + html_content[body_end_idx:]
        else:
            html_content += error_handling_script

    return html_content


@visual.route('/welcome')
def welcome():
    return render_template('visual/welcome.html', title='Welcome')

@visual.route('/index')
@login_required
def index():
    """Display the visualizations gallery."""
    user_visualisations = Visualisation.query.join(Dataset).filter(
        Dataset.user_id == current_user.id
    ).order_by(Visualisation.created_at.desc()).all()
    
    shared_visualisations_query = db.session.query(Visualisation, User.name.label("owner_name")).\
        select_from(Share).\
        join(Visualisation, Share.object_id == Visualisation.id).\
        join(Dataset, Visualisation.dataset_id == Dataset.id).\
        join(User, Dataset.user_id == User.id).\
        filter(
            Share.target_id == current_user.id,
            Share.object_type == 'visualisation'
        ).order_by(Visualisation.created_at.desc())
    
    shared_visualisations_list = [] # Renamed to avoid conflict
    for vis, owner_name in shared_visualisations_query.all():
        shared_visualisations_list.append({
            'id': vis.id,
            'title': vis.title,
            'description': vis.description,
            'created_at': vis.created_at,
            'dataset_filename': vis.dataset.original_filename, 
            'owner_name': owner_name
        })

    return render_template(
        'visual/index.html',
        title='My Dashboards',
        user_visualisations=user_visualisations,
        shared_visualisations=shared_visualisations_list # Use the new list name
    )

@visual.route('/generate/<int:dataset_id>', methods=['GET', 'POST'])
@login_required
def generate(dataset_id):
    """Generate dashboard visualization TEMPLATE for a dataset."""
    dataset = Dataset.query.get_or_404(dataset_id)
    
    # Ensure 'data.index' resolves correctly, otherwise use a known fallback
    data_index_url = url_for('visual.index') # Default fallback
    try:
        data_index_url = url_for('data.index')
    except Exception: # pylint: disable=broad-except
        current_app.logger.warning("'data.index' endpoint not found, falling back to 'visual.index' for redirect.")


    if dataset.user_id != current_user.id: 
        flash('You must own the dataset to generate a new visualization from it.', 'danger')
        return redirect(data_index_url) 
    
    form = GenerateVisualisationForm()
    if form.validate_on_submit():
        room_id = f"user_{current_user.id}" # Define room_id outside try for except block
        try:
            socketio.emit('progress_update', {'percent': 0, 'message': 'Starting dashboard generation...'}, room=room_id)
            current_app.logger.info(f"Starting dashboard template generation for dataset ID: {dataset.id}, title: {form.title.data}")
            
            socketio.emit('progress_update', {'percent': 10, 'message': 'Analyzing dataset structure...'}, room=room_id)
            
            # Use the imported claude_service instance
            dashboard_html_template = claude_service.generate_dashboard(
                dataset.id, 
                form.title.data, 
                form.description.data
            )
            
            prepared_template = prepare_dashboard_template_html(dashboard_html_template) 
            
            socketio.emit('progress_update', {'percent': 90, 'message': 'Dashboard template generated, saving...'}, room=room_id)
            
            visualisation = Visualisation(
                dataset_id=dataset.id,
                title=form.title.data,
                description=form.description.data,
                spec=prepared_template 
            )
            db.session.add(visualisation)
            db.session.commit()
            
            socketio.emit('progress_update', {'percent': 100, 'message': 'Dashboard saved! Redirecting...'}, room=room_id)
            socketio.emit('processing_complete', {'redirect_url': url_for('visual.view', id=visualisation.id)}, room=room_id)
            
            current_app.logger.info(f"Dashboard template generation completed for dataset ID: {dataset.id}")
            flash('Dashboard generated successfully! You can now view it.', 'success')
            return redirect(url_for('visual.view', id=visualisation.id))
            
        except anthropic.APIError as api_err: 
            current_app.logger.error(f"Claude API Error during dashboard generation: {str(api_err)}", exc_info=True)
            socketio.emit('processing_error', {'message': f'Claude API Error: {str(api_err)}'}, room=room_id)
            flash(f'Error communicating with Claude API: {str(api_err)}', 'danger')
        except Exception as e:
            current_app.logger.error(f"Unexpected error in dashboard generation: {str(e)}", exc_info=True)
            socketio.emit('processing_error', {'message': f'Unexpected error: {str(e)}'}, room=room_id)
            flash(f'An unexpected error occurred: {str(e)}', 'danger')
    
    return render_template(
        'visual/generate.html',
        title='Generate Dashboard',
        dataset=dataset,
        form=form
    )

@visual.route('/view/<int:id>')
@login_required
def view(id):
    """View a visualization by injecting data into its template."""
    visualisation = Visualisation.query.get_or_404(id)
    dataset = Dataset.query.get_or_404(visualisation.dataset_id)
    
    can_view = False
    if dataset.user_id == current_user.id or dataset.is_public:
        can_view = True
    else:
        share_record = Share.query.filter_by( # Renamed to avoid conflict
            object_type='visualisation', object_id=id, target_id=current_user.id
        ).first()
        if share_record: # Check if a record was found
            can_view = True
    
    if not can_view:
        flash('You do not have permission to view this dashboard.', 'danger')
        return redirect(url_for('visual.index'))

    actual_dataset_json_for_js = "[]" 
    dashboard_template_html_content = "" # Renamed for clarity

    if visualisation.spec:
        try:
            file_path = dataset.file_path
            if not os.path.exists(file_path):
                current_app.logger.error(f"Dataset file {file_path} not found for visualization {id}.")
                flash('Dataset file is missing. Cannot display dashboard.', 'danger')
            else:
                if dataset.file_type.lower() == 'csv':
                    df = pd.read_csv(file_path)
                elif dataset.file_type.lower() == 'json':
                    df = pd.read_json(file_path)
                else:
                    current_app.logger.error(f"Unsupported dataset type {dataset.file_type} for viz {id}.")
                    flash(f"Unsupported dataset type: {dataset.file_type}", 'danger')
                    df = pd.DataFrame()

                actual_dataset_for_js = df.to_dict(orient='records')
                actual_dataset_json_for_js = json.dumps(actual_dataset_for_js)
            
            dashboard_template_html_content = Markup(visualisation.spec) # Spec is the template

        except Exception as data_err:
            current_app.logger.error(f"Error reading dataset content for visualization {id}: {str(data_err)}", exc_info=True)
            flash('Error loading data for the dashboard. Some elements may not display correctly.', 'warning')
            dashboard_template_html_content = Markup(visualisation.spec) # Still pass template even if data fails
            
    else:
        current_app.logger.warning(f"Empty visualization spec for ID: {id}")
        flash('This dashboard has no content template. It may have been incorrectly generated.', 'warning')
        dashboard_template_html_content = Markup('<html><body><div class="p-4 text-center text-gray-500">No dashboard template available.</div></body></html>')

    return render_template(
        'visual/view.html',
        title=visualisation.title,
        visualisation=visualisation,
        dashboard_template_html=dashboard_template_html_content,
        actual_dataset_json=actual_dataset_json_for_js, 
        dataset=dataset, 
        debug=current_app.debug 
    )

@visual.route('/share/<int:id>', methods=['GET', 'POST'])
@login_required
def share(id):
    """Share a visualization with other users."""
    visualisation = Visualisation.query.get_or_404(id)
    if visualisation.dataset.user_id != current_user.id:
        flash('You can only share dashboards that you own.', 'danger')
        return redirect(url_for('visual.index'))
    
    form = ShareVisualisationForm()
    users = User.query.filter(User.id != current_user.id).order_by(User.name).all()
    form.user_id.choices = [(user.id, f"{user.name} ({user.email})") for user in users]
    
    if form.validate_on_submit():
        target_user_id = form.user_id.data
        target_user = User.query.get(target_user_id)

        if not target_user:
            flash('Selected user not found.', 'danger')
        else:
            existing_share = Share.query.filter_by(
                owner_id=current_user.id,
                target_id=target_user_id,
                object_type='visualisation',
                object_id=id
            ).first()
            
            if existing_share:
                flash(f'This dashboard is already shared with {target_user.name}.', 'warning')
            else:
                new_share = Share( # Renamed to avoid conflict
                    owner_id=current_user.id,
                    target_id=target_user_id,
                    object_type='visualisation',
                    object_id=id
                )
                db.session.add(new_share)
                db.session.commit()
                flash(f'Dashboard shared successfully with {target_user.name}!', 'success')
        return redirect(url_for('visual.share', id=id))
    
    shared_with_users = db.session.query(User).join(Share, Share.target_id == User.id).filter(
        Share.owner_id == current_user.id,
        Share.object_type == 'visualisation',
        Share.object_id == id
    ).all()
    
    return render_template(
        'visual/share.html',
        title=f'Share: {visualisation.title}',
        visualisation=visualisation,
        dataset=visualisation.dataset, 
        form=form,
        shared_with_users=shared_with_users # Renamed from shared_with
    )

@visual.route('/unshare/<int:id>/<int:user_id>', methods=['POST'])
@login_required
def unshare(id, user_id):
    visualisation = Visualisation.query.get_or_404(id)
    if visualisation.dataset.user_id != current_user.id: 
        flash('You can only manage sharing for dashboards that you own.', 'danger')
        return redirect(url_for('visual.index'))
    
    share_to_delete = Share.query.filter_by(
        owner_id=current_user.id,
        target_id=user_id,
        object_type='visualisation',
        object_id=id
    ).first()
    
    if share_to_delete:
        user_removed = User.query.get(user_id)
        db.session.delete(share_to_delete)
        db.session.commit()
        flash(f'Sharing access removed successfully for {user_removed.name if user_removed else "user"}.', 'success')
    else:
        flash('Share record not found or you are not the owner.', 'warning')
    
    return redirect(url_for('visual.share', id=id))

@visual.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    visualisation = Visualisation.query.get_or_404(id)
    if visualisation.dataset.user_id != current_user.id: 
        flash('You can only delete dashboards that you own.', 'danger')
        return redirect(url_for('visual.index'))
    
    Share.query.filter_by(object_type='visualisation', object_id=id).delete(synchronize_session='fetch')
    db.session.delete(visualisation)
    db.session.commit()
    
    flash('Dashboard deleted successfully!', 'success')
    return redirect(url_for('visual.index'))

# API Routes

@visual.route('/api/v1/visualisations', methods=['GET'])
@login_required
@cache.cached(timeout=60) 
def api_get_visualisations():
    visualisations = Visualisation.query.join(Dataset).filter(
        Dataset.user_id == current_user.id
    ).order_by(Visualisation.created_at.desc()).all()
    
    result = [{
        'id': vis.id, 'title': vis.title, 'description': vis.description,
        'dataset_name': vis.dataset.original_filename, 
        'created_at': vis.created_at.isoformat()
    } for vis in visualisations]
    return jsonify(visualisations=result)

@visual.route('/api/v1/shared-visualisations', methods=['GET'])
@login_required
@cache.cached(timeout=60)
def api_get_shared_visualisations():
    shared_visualisations_data = db.session.query( # Renamed
            Visualisation, User.name.label("owner_name")
        ).\
        select_from(Share).\
        join(Visualisation, Share.object_id == Visualisation.id).\
        join(Dataset, Visualisation.dataset_id == Dataset.id).\
        join(User, Dataset.user_id == User.id).\
        filter(
            Share.target_id == current_user.id,
            Share.object_type == 'visualisation'
        ).order_by(Visualisation.created_at.desc()).all()
    
    result = [{
        'id': vis.id, 'title': vis.title, 'description': vis.description,
        'dataset_name': vis.dataset.original_filename,
        'created_at': vis.created_at.isoformat(),
        'owner_name': owner_name
    } for vis, owner_name in shared_visualisations_data] # Use renamed variable
    return jsonify(visualisations=result)


@visual.route('/api/v1/visualisations/<int:id>', methods=['GET'])
@login_required
@cache.cached(timeout=60) 
def api_get_visualisation(id):
    visualisation = Visualisation.query.get_or_404(id)
    dataset = Dataset.query.get_or_404(visualisation.dataset_id)
    
    can_view = False
    if dataset.user_id == current_user.id or dataset.is_public:
        can_view = True
    else:
        share_record_api = Share.query.filter_by(object_type='visualisation', object_id=id, target_id=current_user.id).first() # Renamed
        if share_record_api: can_view = True # Use renamed variable
    
    if not can_view:
        return jsonify(error='Permission denied'), 403

    actual_data_for_js = []
    try:
        file_path = dataset.file_path
        if os.path.exists(file_path):
            if dataset.file_type.lower() == 'csv':
                df = pd.read_csv(file_path)
            elif dataset.file_type.lower() == 'json':
                df = pd.read_json(file_path)
            else: df = pd.DataFrame()
            actual_data_for_js = df.to_dict(orient='records')
        else:
             current_app.logger.warning(f"API: Dataset file {file_path} not found for viz {id}")
    except Exception as e:
        current_app.logger.error(f"API: Error loading data for viz {id}: {e}", exc_info=True)

    return jsonify(
        id=visualisation.id,
        title=visualisation.title,
        description=visualisation.description,
        dashboard_template_spec=visualisation.spec, 
        actual_dataset=actual_data_for_js, 
        dataset_id=visualisation.dataset_id,
        dataset_filename=dataset.original_filename,
        created_at=visualisation.created_at.isoformat()
    )