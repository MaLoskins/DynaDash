from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, g
from flask_login import login_required, current_user
from flask_socketio import emit
from markupsafe import Markup
from . import visual
from ...models import db, Dataset, Visualisation, Share, User
from .forms import GenerateVisualisationForm, ShareVisualisationForm
from ...services.claude_client import ClaudeClient
from ... import cache
import traceback
import re

# Initialize the Claude client service
claude_client = ClaudeClient()

@visual.route('/welcome')
def welcome():
    return render_template('visual/welcome.html', title='Welcome')

@visual.route('/index')
@login_required
def index():
    """Display the visualizations gallery."""
    # Get user's visualizations
    user_visualisations = Visualisation.query.join(Dataset).filter(
        Dataset.user_id == current_user.id
    ).order_by(Visualisation.created_at.desc()).all()
    
    # Get visualizations shared with the user
    shared_visualisations = db.session.query(Visualisation).\
        select_from(Share).\
        join(Visualisation, Share.object_id == Visualisation.id).\
        filter(
            Share.target_id == current_user.id,
            Share.object_type == 'visualisation'
        ).order_by(Visualisation.created_at.desc()).all()
    
    return render_template(
        'visual/index.html',
        title='My Dashboards',
        user_visualisations=user_visualisations,
        shared_visualisations=shared_visualisations
    )

@visual.route('/generate/<int:dataset_id>', methods=['GET', 'POST'])
@login_required
def generate(dataset_id):
    """Generate dashboard visualization for a dataset."""
    dataset = Dataset.query.get_or_404(dataset_id)
    
    # Check if the user has access to this dataset
    if dataset.user_id != current_user.id and not dataset.is_public:
        # Check if the dataset is shared with the user
        share = Share.query.filter_by(
            object_type='dataset',
            object_id=dataset.id,
            target_id=current_user.id
        ).first()
        
        if not share:
            flash('You do not have permission to visualize this dataset.', 'danger')
            return redirect(url_for('data.index'))
    
    form = GenerateVisualisationForm()
    if form.validate_on_submit():
        # Start the dashboard generation process
        try:
            # Emit a socket event to start the progress bar
            from ... import socketio
            socketio.emit('progress_update', {'percent': 0, 'message': 'Starting dashboard generation...'}, room=current_user.id)
            current_app.logger.info(f"Starting dashboard generation for dataset ID: {dataset.id}, title: {form.title.data}")
            
            # Emit progress update
            socketio.emit('progress_update', {'percent': 10, 'message': 'Preparing dataset for analysis...'}, room=current_user.id)
            
            # Generate the dashboard using Claude
            try:
                dashboard_html = claude_client.generate_dashboard(
                    dataset.id, 
                    form.title.data, 
                    form.description.data
                )
                
                # Validate and clean the HTML
                dashboard_html = clean_dashboard_html(dashboard_html)
                
                # Emit progress update
                socketio.emit('progress_update', {'percent': 90, 'message': 'Dashboard generated, saving...'}, room=current_user.id)
                
                # Create a new visualization record
                visualisation = Visualisation(
                    dataset_id=dataset.id,
                    title=form.title.data,
                    description=form.description.data,
                    spec=dashboard_html
                )
                db.session.add(visualisation)
                db.session.commit()
                
                # Emit a socket event to complete the progress bar
                socketio.emit('progress_update', {'percent': 100, 'message': 'Dashboard completed!'}, room=current_user.id)
                socketio.emit('processing_complete', room=current_user.id)
                
                current_app.logger.info(f"Dashboard generation completed successfully for dataset ID: {dataset.id}")
                flash('Dashboard generated successfully!', 'success')
                return redirect(url_for('visual.view', id=visualisation.id))
            except Exception as api_error:
                current_app.logger.error(f"API Error in dashboard generation: {str(api_error)}")
                current_app.logger.error(traceback.format_exc())
                socketio.emit('processing_error', {'message': str(api_error)}, room=current_user.id)
                flash(f'Error in Claude API: {str(api_error)}', 'danger')
                return render_template(
                    'visual/generate.html',
                    title='Generate Dashboard',
                    dataset=dataset,
                    form=form
                )
        
        except Exception as e:
            current_app.logger.error(f"Unexpected error in dashboard generation: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            flash(f'Unexpected error: {str(e)}', 'danger')
    
    return render_template(
        'visual/generate.html',
        title='Generate Dashboard',
        dataset=dataset,
        form=form
    )

def clean_dashboard_html(html_content):
    """Clean and validate the dashboard HTML to ensure it's suitable for iframe display."""
    if not html_content:
        current_app.logger.warning("Empty HTML content provided to clean_dashboard_html")
        return "<html><body><h2>No dashboard content available</h2></body></html>"
    
    # Ensure the HTML starts with doctype
    if not html_content.strip().startswith("<!DOCTYPE"):
        html_content = "<!DOCTYPE html>\n" + html_content
    
    # Make sure it has proper HTML, head, and body tags
    if "<html" not in html_content:
        html_content = re.sub(r'<!DOCTYPE[^>]*>', '<!DOCTYPE html>\n<html>', html_content)
        html_content += "\n</html>"
    
    if "<head" not in html_content:
        html_content = re.sub(r'<html[^>]*>', '<html>\n<head><meta charset="UTF-8"><title>Dashboard</title></head>', html_content)
    
    if "<body" not in html_content:
        html_content = re.sub(r'</head>', '</head>\n<body>', html_content)
        html_content = re.sub(r'</html>', '</body>\n</html>', html_content)
    
    # Ensure valid closing tags
    if not re.search(r'</body>', html_content):
        html_content = re.sub(r'</html>', '</body>\n</html>', html_content)
    
    # Replace any potential harmful attributes
    html_content = re.sub(r'on\w+\s*=', 'data-disabled-event=', html_content)
    
    # Fix common invalid HTML issues
    html_content = html_content.replace('&lt;', '<').replace('&gt;', '>')
    
    # Add viewport meta tag for better responsiveness inside iframe
    if '<head>' in html_content and '<meta name="viewport"' not in html_content:
        viewport_meta = '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">'
        html_content = html_content.replace('<head>', f'<head>\n    {viewport_meta}')
    
    # Add CSS for better display in iframe - with improved width handling
    if '</head>' in html_content:
        responsive_css = """
<style>
    /* Reset all elements */
    * {
        box-sizing: border-box !important;
    }
    
    /* Base styles for the whole document */
    html, body {
        width: 100% !important;
        height: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow-x: hidden !important;
    }
    
    /* Main content container */
    #dashboard-content,
    #root,
    #app,
    main,
    .main,
    .dashboard,
    .dashboard-main {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 auto !important;
    }
    
    /* Fix for all container elements to use full width */
    .container, 
    .row,
    .dashboard-container, 
    .chart-container, 
    div[class*="container"],
    section,
    article,
    .card,
    .panel,
    .box {
        width: 100% !important;
        max-width: 100% !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    
    /* Ensure all charts resize properly */
    canvas, 
    svg,
    .chart,
    div[class*="chart"] {
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* Grid system fixes */
    .row, 
    .grid, 
    div[class*="row"], 
    div[class*="grid"] {
        display: flex !important;
        flex-wrap: wrap !important;
        width: 100% !important;
    }
    
    /* Column fixes */
    .col, 
    .column, 
    div[class*="col-"], 
    div[class*="column-"] {
        padding-left: 10px !important;
        padding-right: 10px !important;
    }
    
    /* Specific column widths */
    .col-12, .col-sm-12, .col-md-12, .col-lg-12, .col-xl-12 {
        flex: 0 0 100% !important;
        max-width: 100% !important;
    }
    
    .col-6, .col-sm-6, .col-md-6, .col-lg-6, .col-xl-6 {
        flex: 0 0 50% !important;
        max-width: 50% !important;
    }
    
    .col-4, .col-sm-4, .col-md-4, .col-lg-4, .col-xl-4 {
        flex: 0 0 33.333% !important;
        max-width: 33.333% !important;
    }
    
    .col-3, .col-sm-3, .col-md-3, .col-lg-3, .col-xl-3 {
        flex: 0 0 25% !important;
        max-width: 25% !important;
    }
    
    /* Important: Override width attributes and fixed width styles */
    [style*="width:"], 
    [style*="max-width:"],
    [width] {
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* Ensure content doesn't overflow its container */
    img, table {
        max-width: 100% !important;
        height: auto !important;
    }
    
    /* Add responsive script to the page */
</style>
<script>
    document.addEventListener('DOMContentLoaded', function() {
        // Function to resize all fixed-width elements
        function makeResponsive() {
            // Find all elements with explicit width style or attribute
            const fixedWidthElements = document.querySelectorAll('[style*="width"],[width]');
            fixedWidthElements.forEach(element => {
                // Override with responsive width
                element.style.width = '100%';
                element.style.maxWidth = '100%';
                if (element.hasAttribute('width')) {
                    element.removeAttribute('width');
                }
            });
            
            // Make sure charts are responsive
            const chartContainers = document.querySelectorAll('.chart-container, [class*="-chart-container"]');
            chartContainers.forEach(container => {
                container.style.width = '100%';
                container.style.maxWidth = '100%';
                
                // If it contains a canvas, make that responsive too
                const canvas = container.querySelector('canvas');
                if (canvas) {
                    canvas.style.width = '100%';
                    canvas.style.maxWidth = '100%';
                }
            });
        }
        
        // Run on load and resize
        makeResponsive();
        window.addEventListener('resize', makeResponsive);
    });
</script>
"""
        html_content = html_content.replace('</head>', f'{responsive_css}</head>')
    
    # Add sandbox and CSP meta tags for extra security
    if '<head>' in html_content and '<meta http-equiv="Content-Security-Policy"' not in html_content:
        csp_tag = '<meta http-equiv="Content-Security-Policy" content="default-src \'self\' cdn.jsdelivr.net cdnjs.cloudflare.com; script-src \'self\' \'unsafe-inline\' cdn.jsdelivr.net cdnjs.cloudflare.com; style-src \'self\' \'unsafe-inline\' cdn.jsdelivr.net cdnjs.cloudflare.com;">'
        html_content = html_content.replace('<head>', f'<head>\n    {csp_tag}')
    
    # Fix any HTML lang attribute issues (Claude sometimes generates weird ones)
    html_content = re.sub(r'<html lang="\s*en\s*"="">', '<html lang="en">', html_content)
    
    return html_content

@visual.route('/view/<int:id>')
@login_required
def view(id):
    """View a visualization."""
    visualisation = Visualisation.query.get_or_404(id)
    dataset = Dataset.query.get(visualisation.dataset_id)
    
    # Check if the user has access to this visualization
    if dataset.user_id != current_user.id and not dataset.is_public:
        # Check if the visualization is shared with the user
        share = Share.query.filter_by(
            object_type='visualisation',
            object_id=visualisation.id,
            target_id=current_user.id
        ).first()
        
        if not share:
            flash('You do not have permission to view this dashboard.', 'danger')
            return redirect(url_for('visual.index'))
    
    # Ensure the visualization spec is properly marked as safe HTML
    try:
        if visualisation.spec:
            # Clean the HTML before sending it to the template
            cleaned_html = clean_dashboard_html(visualisation.spec)
            vis_html = Markup(cleaned_html)
        else:
            current_app.logger.warning(f"Empty visualization spec for ID: {id}")
            flash('This dashboard has no content. It may have been incorrectly generated.', 'warning')
            vis_html = Markup('<html><body><div class="p-4 text-center text-gray-500">No dashboard content available</div></body></html>')
    except Exception as e:
        current_app.logger.error(f"Error processing visualization spec: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        vis_html = Markup('<html><body><div class="p-4 text-center text-red-500">Error loading dashboard content</div></body></html>')
    
    return render_template(
        'visual/view.html',
        title=visualisation.title,
        visualisation=visualisation,
        vis_html=vis_html,
        dataset=dataset,
        debug=current_app.debug
    )

@visual.route('/share/<int:id>', methods=['GET', 'POST'])
@login_required
def share(id):
    """Share a visualization with other users."""
    visualisation = Visualisation.query.get_or_404(id)
    dataset = Dataset.query.get(visualisation.dataset_id)
    
    # Check if the user owns this visualization
    if dataset.user_id != current_user.id:
        flash('You can only share dashboards that you own.', 'danger')
        return redirect(url_for('visual.index'))
    
    form = ShareVisualisationForm()
    
    # Get all users except the current user for the form choices
    users = User.query.filter(User.id != current_user.id).all()
    form.user_id.choices = [(user.id, user.name) for user in users]
    
    if form.validate_on_submit():
        user_id = form.user_id.data
        
        # Check if the share already exists
        existing_share = Share.query.filter_by(
            owner_id=current_user.id,
            target_id=user_id,
            object_type='visualisation',
            object_id=visualisation.id
        ).first()
        
        if existing_share:
            flash('This dashboard is already shared with this user.', 'warning')
        else:
            share = Share(
                owner_id=current_user.id,
                target_id=user_id,
                object_type='visualisation',
                object_id=visualisation.id
            )
            db.session.add(share)
            db.session.commit()
            flash('Dashboard shared successfully!', 'success')
        
        return redirect(url_for('visual.share', id=id))
    
    # Get all users this visualization is shared with
    shared_with = db.session.query(User).join(
        Share,
        Share.target_id == User.id
    ).filter(
        Share.owner_id == current_user.id,
        Share.object_type == 'visualisation',
        Share.object_id == visualisation.id
    ).all()
    
    return render_template(
        'visual/share.html',
        title=f'Share Dashboard: {visualisation.title}',
        visualisation=visualisation,
        form=form,
        shared_with=shared_with,
        dataset=dataset
    )

@visual.route('/unshare/<int:id>/<int:user_id>', methods=['POST'])
@login_required
def unshare(id, user_id):
    """Remove sharing access for a user."""
    visualisation = Visualisation.query.get_or_404(id)
    dataset = Dataset.query.get(visualisation.dataset_id)
    
    # Check if the user owns this visualization
    if dataset.user_id != current_user.id:
        flash('You can only manage sharing for dashboards that you own.', 'danger')
        return redirect(url_for('visual.index'))
    
    share = Share.query.filter_by(
        owner_id=current_user.id,
        target_id=user_id,
        object_type='visualisation',
        object_id=visualisation.id
    ).first_or_404()
    
    db.session.delete(share)
    db.session.commit()
    flash('Sharing access removed successfully!', 'success')
    
    return redirect(url_for('visual.share', id=id))

@visual.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete a visualization."""
    visualisation = Visualisation.query.get_or_404(id)
    dataset = Dataset.query.get(visualisation.dataset_id)
    
    # Check if the user owns this visualization
    if dataset.user_id != current_user.id:
        flash('You can only delete dashboards that you own.', 'danger')
        return redirect(url_for('visual.index'))
    
    # Delete all shares for this visualization
    Share.query.filter_by(object_type='visualisation', object_id=visualisation.id).delete()
    
    # Delete the visualization record
    db.session.delete(visualisation)
    db.session.commit()
    
    flash('Dashboard deleted successfully!', 'success')
    return redirect(url_for('visual.index'))

# API Routes

@visual.route('/api/v1/visualisations', methods=['GET'])
@login_required
@cache.cached(timeout=300)  # Cache for 5 minutes
def api_get_visualisations():
    """API endpoint to get all visualizations for the current user."""
    visualisations = Visualisation.query.join(Dataset).filter(
        Dataset.user_id == current_user.id
    ).order_by(Visualisation.created_at.desc()).all()
    
    result = []
    for vis in visualisations:
        dataset = Dataset.query.get(vis.dataset_id)
        result.append({
            'id': vis.id,
            'title': vis.title,
            'description': vis.description,
            'dataset_name': dataset.original_filename,
            'created_at': vis.created_at.isoformat()
        })
    
    return jsonify(visualisations=result)

@visual.route('/api/v1/shared-visualisations', methods=['GET'])
@login_required
@cache.cached(timeout=300)  # Cache for 5 minutes
def api_get_shared_visualisations():
    """API endpoint to get all visualizations shared with the current user."""
    shared_visualisations = db.session.query(Visualisation).\
        select_from(Share).\
        join(Visualisation, Share.object_id == Visualisation.id).\
        filter(
            Share.target_id == current_user.id,
            Share.object_type == 'visualisation'
        ).order_by(Visualisation.created_at.desc()).all()
    
    result = []
    for vis in shared_visualisations:
        dataset = Dataset.query.get(vis.dataset_id)
        owner = User.query.get(dataset.user_id)
        result.append({
            'id': vis.id,
            'title': vis.title,
            'description': vis.description,
            'dataset_name': dataset.original_filename,
            'created_at': vis.created_at.isoformat(),
            'owner': owner.name if owner else 'Unknown'
        })
    
    return jsonify(visualisations=result)

@visual.route('/api/v1/generate', methods=['POST'])
@login_required
def api_generate():
    """API endpoint for dashboard generation."""
    data = request.get_json()
    if not data:
        return jsonify(error='No data provided'), 400
    
    dataset_id = data.get('dataset_id')
    title = data.get('title')
    description = data.get('description', '')
    
    if not dataset_id or not title:
        return jsonify(error='Dataset ID and title are required'), 400
    
    dataset = Dataset.query.get_or_404(dataset_id)
    
    # Check if the user has access to this dataset
    if dataset.user_id != current_user.id and not dataset.is_public:
        # Check if the dataset is shared with the user
        share = Share.query.filter_by(
            object_type='dataset',
            object_id=dataset.id,
            target_id=current_user.id
        ).first()
        
        if not share:
            return jsonify(error='You do not have permission to visualize this dataset.'), 403
    
    try:
        # Generate the dashboard using Claude
        dashboard_html = claude_client.generate_dashboard(dataset_id, title, description)
        
        # Clean and validate the HTML
        dashboard_html = clean_dashboard_html(dashboard_html)
        
        # Create a new visualization record
        visualisation = Visualisation(
            dataset_id=dataset_id,
            title=title,
            description=description,
            spec=dashboard_html
        )
        db.session.add(visualisation)
        db.session.commit()
        
        return jsonify(
            success=True,
            visualisation_id=visualisation.id,
            message='Dashboard generated successfully!'
        )
    
    except Exception as e:
        current_app.logger.error(f"API error in dashboard generation: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify(error=f'Error generating dashboard: {str(e)}'), 500

@visual.route('/api/v1/visualisations/<int:id>', methods=['GET'])
@login_required
@cache.cached(timeout=120)  # Cache for 2 minutes
def api_get_visualisation(id):
    """API endpoint to get a specific visualization."""
    visualisation = Visualisation.query.get_or_404(id)
    dataset = Dataset.query.get(visualisation.dataset_id)
    
    # Check if the user has access to this visualization
    if dataset.user_id != current_user.id and not dataset.is_public:
        # Check if the visualization is shared with the user
        share = Share.query.filter_by(
            object_type='visualisation',
            object_id=visualisation.id,
            target_id=current_user.id
        ).first()
        
        if not share:
            return jsonify(error='You do not have permission to view this dashboard.'), 403
    
    return jsonify(
        id=visualisation.id,
        title=visualisation.title,
        description=visualisation.description,
        spec=visualisation.spec,
        dataset_id=visualisation.dataset_id,
        created_at=visualisation.created_at.isoformat()
    )