use wasm_bindgen::prelude::*;
use wasm_bindgen_futures::JsFuture;
use web_sys::{Request, RequestInit, RequestMode, Response};
use js_sys::JSON;
use serde::{Deserialize, Serialize};

// ── Data Models ──────────────────────────────────────────────────────────────

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Activity {
    pub id: i64,
    pub activity_id: String,
    pub start_time: Option<String>,
    pub end_time: Option<String>,
    pub distance_meters: Option<f64>,
    pub duration_seconds: Option<i64>,
    pub avg_pace_seconds_per_km: Option<f64>,
    pub calories: Option<i64>,
    pub avg_heart_rate: Option<i64>,
    pub max_heart_rate: Option<i64>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct StepEntry {
    pub date: String,
    pub step_count: i64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct StepStatistics {
    pub analysis_date: String,
    pub start_date: String,
    pub end_date: String,
    pub days_analyzed: i64,
    pub average_steps: f64,
    pub max_steps: i64,
    pub min_steps: i64,
    pub standard_deviation: f64,
}

// ── API Helpers ───────────────────────────────────────────────────────────────

async fn fetch_json(url: &str) -> Result<JsValue, JsValue> {
    let opts = RequestInit::new();
    opts.set_method("GET");
    opts.set_mode(RequestMode::Cors);

    let request = Request::new_with_str_and_init(url, &opts)?;
    let window = web_sys::window().unwrap();
    let resp_value = JsFuture::from(window.fetch_with_request(&request)).await?;
    let resp: Response = resp_value.dyn_into()?;
    let json = JsFuture::from(resp.json()?).await?;
    Ok(json)
}

async fn post_json(url: &str, body: &str) -> Result<JsValue, JsValue> {
    let opts = RequestInit::new();
    opts.set_method("POST");
    opts.set_mode(RequestMode::Cors);
    opts.set_body(&JsValue::from_str(body));

    let request = Request::new_with_str_and_init(url, &opts)?;
    request.headers().set("Content-Type", "application/json")?;

    let window = web_sys::window().unwrap();
    let resp_value = JsFuture::from(window.fetch_with_request(&request)).await?;
    let resp: Response = resp_value.dyn_into()?;
    let json = JsFuture::from(resp.json()?).await?;
    Ok(json)
}

// ── DOM Helpers ───────────────────────────────────────────────────────────────

fn document() -> web_sys::Document {
    web_sys::window().unwrap().document().unwrap()
}

fn get_element(id: &str) -> web_sys::Element {
    document().get_element_by_id(id).unwrap()
}

fn set_inner_html(id: &str, html: &str) {
    get_element(id).set_inner_html(html);
}

// ── Rendering ─────────────────────────────────────────────────────────────────

fn render_activities(activities: &[Activity]) {
    if activities.is_empty() {
        set_inner_html("activities-list", "<p class=\"empty\">No activities found. Try syncing.</p>");
        return;
    }

    let mut html = String::new();
    for act in activities {
        let distance = act.distance_meters.map(|d| format!("{:.2} km", d / 1000.0)).unwrap_or_default();
        let duration = act.duration_seconds.map(|s| format!("{:.0} min", s as f64 / 60.0)).unwrap_or_default();
        let pace = act.avg_pace_seconds_per_km.map(|p| {
            let mins = (p / 60.0).floor() as i64;
            let secs = (p % 60.0).round() as i64;
            format!("{:02}:{:02} /km", mins, secs)
        }).unwrap_or_default();
        let date = act.start_time.as_deref().unwrap_or("Unknown date").get(..10).unwrap_or("Unknown");
        let hr = act.avg_heart_rate.map(|h| format!("{} bpm", h)).unwrap_or_else(|| "—".into());
        let cal = act.calories.map(|c| format!("{} kcal", c)).unwrap_or_else(|| "—".into());

        html.push_str(&format!(
            r#"<div class="card" data-id="{id}">
                <div class="card-header">
                    <span class="date">{date}</span>
                    <span class="distance">{distance}</span>
                </div>
                <div class="card-body">
                    <div class="stat"><span class="label">Duration</span><span class="value">{duration}</span></div>
                    <div class="stat"><span class="label">Pace</span><span class="value">{pace}</span></div>
                    <div class="stat"><span class="label">Avg HR</span><span class="value">{hr}</span></div>
                    <div class="stat"><span class="label">Calories</span><span class="value">{cal}</span></div>
                </div>
            </div>"#,
            id = act.id,
            date = date,
            distance = distance,
            duration = duration,
            pace = pace,
            hr = hr,
            cal = cal,
        ));
    }
    set_inner_html("activities-list", &html);
}

fn render_steps(steps: &[StepEntry], stats: Option<&StepStatistics>) {
    // Statistics banner
    if let Some(s) = stats {
        set_inner_html("steps-stats", &format!(
            r#"<div class="stats-row">
                <div class="stat-box"><span class="label">Avg Steps</span><span class="value">{:.0}</span></div>
                <div class="stat-box"><span class="label">Min</span><span class="value">{}</span></div>
                <div class="stat-box"><span class="label">Max</span><span class="value">{}</span></div>
                <div class="stat-box"><span class="label">Standard Deviation</span><span class="value">{:.0}</span></div>
            </div>"#,
            s.average_steps, s.max_steps, s.min_steps, s.standard_deviation
        ));
    }

    if steps.is_empty() {
        set_inner_html("steps-chart", "<p class=\"empty\">No step data found. Try syncing.</p>");
        return;
    }

    let max_steps = steps.iter().map(|s| s.step_count).max().unwrap_or(1);

    let mut bars = String::new();
    for entry in steps {
        let height_pct = (entry.step_count as f64 / max_steps as f64 * 100.0).round() as i64;
        let label = entry.date.get(5..).unwrap_or(&entry.date); // MM-DD
        let formatted_count = format_number_with_commas(entry.step_count);
        bars.push_str(&format!(
            r#"<div class="bar-wrap">
                <div class="bar-value">{value}</div>
                <div class="bar" style="height: {height}%;" title="{count} steps on {date}"></div>
                <div class="bar-label">{label}</div>
            </div>"#,
            value = formatted_count,
            height = height_pct,
            count = entry.step_count,
            date = entry.date,
            label = label,
        ));
    }

    set_inner_html("steps-chart", &format!(r#"<div class="bar-chart">{}</div>"#, bars));
}

fn show_loading(id: &str, msg: &str) {
    set_inner_html(id, &format!(r#"<div class="loading"><div class="spinner"></div><span>{}</span></div>"#, msg));
}

fn show_error(id: &str, msg: &str) {
    set_inner_html(id, &format!(r#"<p class="error">⚠ {}</p>"#, msg));
}

fn format_number_with_commas(n: i64) -> String {
    let s = n.to_string();
    let mut result = String::new();
    for (i, c) in s.chars().rev().enumerate() {
        if i > 0 && i % 3 == 0 {
            result.push(',');
        }
        result.push(c);
    }
    result.chars().rev().collect()
}

// ── Entry Point ───────────────────────────────────────────────────────────────

#[wasm_bindgen(start)]
pub async fn main() -> Result<(), JsValue> {
    console_error_panic_hook();
    load_activities().await?;
    load_steps().await?;

    // Wire up sync buttons
    let doc = document();

    let sync_activities_btn = doc.get_element_by_id("sync-activities-btn").unwrap();
    let sync_activities_closure = Closure::wrap(Box::new(move || {
        wasm_bindgen_futures::spawn_local(async {
            let _ = do_sync_activities().await;
        });
    }) as Box<dyn Fn()>);
    sync_activities_btn
        .dyn_ref::<web_sys::HtmlButtonElement>()
        .unwrap()
        .set_onclick(Some(sync_activities_closure.as_ref().unchecked_ref()));
    sync_activities_closure.forget();

    let sync_steps_btn = doc.get_element_by_id("sync-steps-btn").unwrap();
    let sync_steps_closure = Closure::wrap(Box::new(move || {
        wasm_bindgen_futures::spawn_local(async {
            let _ = do_sync_steps().await;
        });
    }) as Box<dyn Fn()>);
    sync_steps_btn
        .dyn_ref::<web_sys::HtmlButtonElement>()
        .unwrap()
        .set_onclick(Some(sync_steps_closure.as_ref().unchecked_ref()));
    sync_steps_closure.forget();

    Ok(())
}

fn console_error_panic_hook() {
    #[cfg(feature = "console_error_panic_hook")]
    console_error_panic_hook::set_once();
}

async fn load_activities() -> Result<(), JsValue> {
    show_loading("activities-list", "Loading activities…");
    match fetch_json("/api/activities/").await {
        Ok(json) => {
            let activities: Vec<Activity> = serde_wasm_bindgen::from_value(json)
                .map_err(|e| JsValue::from_str(&format!("{:?}", e)))?;
            render_activities(&activities);
        }
        Err(e) => {
            let msg = JSON::stringify(&e).map(|s| s.as_string().unwrap_or_default()).unwrap_or_default();
            show_error("activities-list", &format!("Failed to load activities: {}", msg));
        }
    }
    Ok(())
}

async fn load_steps() -> Result<(), JsValue> {
    show_loading("steps-chart", "Loading step data…");

    let stats = fetch_json("/api/steps/statistics").await.ok().and_then(|json| {
        serde_wasm_bindgen::from_value::<StepStatistics>(json).ok()
    });

    match fetch_json("/api/steps/").await {
        Ok(json) => {
            let steps: Vec<StepEntry> = serde_wasm_bindgen::from_value(json)
                .map_err(|e| JsValue::from_str(&format!("{:?}", e)))?;
            render_steps(&steps, stats.as_ref());
        }
        Err(e) => {
            let msg = JSON::stringify(&e).map(|s| s.as_string().unwrap_or_default()).unwrap_or_default();
            show_error("steps-chart", &format!("Failed to load steps: {}", msg));
        }
    }
    Ok(())
}

async fn do_sync_activities() -> Result<(), JsValue> {
    show_loading("activities-list", "Syncing from Garmin Connect…");
    match post_json("/api/activities/sync", r#"{"days_back": 30}"#).await {
        Ok(_) => load_activities().await,
        Err(e) => {
            let msg = JSON::stringify(&e).map(|s| s.as_string().unwrap_or_default()).unwrap_or_default();
            show_error("activities-list", &format!("Sync failed: {}", msg));
            Ok(())
        }
    }
}

async fn do_sync_steps() -> Result<(), JsValue> {
    show_loading("steps-chart", "Syncing step data from Garmin Connect…");
    match post_json("/api/steps/sync", r#"{"days_back": 30}"#).await {
        Ok(_) => load_steps().await,
        Err(e) => {
            let msg = JSON::stringify(&e).map(|s| s.as_string().unwrap_or_default()).unwrap_or_default();
            show_error("steps-chart", &format!("Sync failed: {}", msg));
            Ok(())
        }
    }
}
