/* ================= PASSWORD STRENGTH ================= */

function checkStrength(){

let pass = document.getElementById("pass");
let strengthText = document.getElementById("strengthText");

let value = pass.value;

let strength = 0;

if(value.length >= 6) strength++;
if(/[A-Z]/.test(value)) strength++;
if(/[a-z]/.test(value)) strength++;
if(/[0-9]/.test(value)) strength++;
if(/[^A-Za-z0-9]/.test(value)) strength++;

if(strength <= 2){
pass.style.borderBottom = "3px solid red";
strengthText.innerHTML = "Weak Password";
strengthText.style.color = "red";
}
else if(strength === 3){
pass.style.borderBottom = "3px solid orange";
strengthText.innerHTML = "Medium Strength";
strengthText.style.color = "orange";
}
else{
pass.style.borderBottom = "3px solid #00c851";
strengthText.innerHTML = "Strong Password";
strengthText.style.color = "#00c851";
}

}

/* ================= PHONE VALIDATION ================= */

function validatePhone(){

let phone = document.getElementById("phone");

if(phone.value.length != 10){
phone.style.borderBottom = "3px solid red";
}else{
phone.style.borderBottom = "3px solid #00c851";
}

}

/* ================= FORM VALIDATION ================= */

function validatePassword(){

let pass = document.getElementById("pass").value;
let confirm = document.getElementById("confirm").value;

let strongRegex =
/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{6,}$/;

if(!strongRegex.test(pass)){
alert("Password must contain uppercase, lowercase, number and symbol");
return false;
}

if(pass !== confirm){
alert("Passwords do not match");
return false;
}

return true;
}

/* ================= IMAGE PREVIEW ================= */

function previewImage(){

    let fileInput = document.getElementById("imageInput");
    let file = fileInput.files[0];

    if(!file) return;

    // Clear previous results
    document.getElementById("diag").innerText = "--";
    document.getElementById("conf").innerText = "--";
    document.getElementById("cdr").innerText = "--";

    document.querySelector(".result").style.display = "none";
    document.getElementById("analyzeBtn").disabled = true;

    // Show preview
    let reader = new FileReader();
    reader.onload = function(e){
        document.getElementById("preview").src = e.target.result;
    };
    reader.readAsDataURL(file);

    // 🔥 Automatic Validation
    let formData = new FormData();
    formData.append("image", file);

    fetch("/validate",{
        method:"POST",
        body:formData
    })
    .then(response => response.json())
    .then(data => {

        let msg = document.getElementById("validationMsg");

        if(data.status === "valid"){
            msg.innerHTML = "✅ Retinal fundus image validated";
            msg.style.color = "green";
            document.getElementById("analyzeBtn").disabled = false;
        }
        else if(data.status === "invalid"){
            msg.innerHTML = "❌ Not a valid retinal fundus image";
            msg.style.color = "red";
        }
        else{
            msg.innerHTML = "⚠ Validation error";
            msg.style.color = "orange";
        }

    })
    .catch(error=>{
        console.error(error);
    });
}
/* ================= ANALYZE IMAGE ================= */

function analyzeImage(){

    let fileInput = document.getElementById("imageInput");
    let file = fileInput.files[0];

    if(!file){
        alert("Please upload an image first");
        return;
    }

    let loader = document.getElementById("loader");
    if(loader) loader.style.display = "block";

    let formData = new FormData();
    formData.append("image", file);
    formData.append("eyeType", document.getElementById("eyeType").value);
    fetch("/predict",{
        method:"POST",
        body:formData
    })
    .then(response => response.json())
    .then(data => {

        if(loader) loader.style.display = "none";

        let resultBox = document.querySelector(".result");

        // 🔴 Handle invalid retinal image
        if(data.status === "invalid"){
            alert(data.message);
            if(resultBox) resultBox.style.display = "none";
            return;  // STOP here (important)
        }

        // 🔴 Handle server error
        if(data.status === "error"){
            alert(data.message);
            if(resultBox) resultBox.style.display = "none";
            return;
        }

        // 🟢 Handle success
if(data.status === "success"){

    document.getElementById("diag").innerText = data.result;
    document.getElementById("conf").innerText = data.confidence + "%";
    document.getElementById("cdr").innerText = data.cdr !== null ? data.cdr : "N/A";

    if(resultBox) resultBox.style.display = "block";

    // 🔥 Show download button
    let downloadBtn = document.getElementById("downloadBtn");
    if(downloadBtn){
    downloadBtn.style.display = "block";
}

    // Save result globally
    window.latestResult = data;

    // Click event
    downloadBtn.onclick = function(){

        if(data.result === "Glaucoma"){
            openQuestionnaire();
        } else {
            generateReport();
        }
    };
  }
    })  
    .catch(error => {

    console.error("js Error:", error);

    let loader = document.getElementById("loader");
    if(loader) loader.style.display = "none";

    alert("Server error occurred. Check Flask console.");
});
}
function openQuestionnaire(){
    document.getElementById("questionModal").style.display = "flex";
}

function submitQuestionnaire(){

    let riskScore = 0;

    if(document.getElementById("ageRisk").checked) riskScore += 1;
    if(document.getElementById("familyHistory").checked) riskScore += 1;
    if(document.getElementById("eyePain").checked) riskScore += 1;
    if(document.getElementById("blurredVision").checked) riskScore += 1;
    if(document.getElementById("watering").checked) riskScore += 1;

    document.getElementById("questionModal").style.display = "none";

    generateReport(riskScore);
}
function generateReport(riskScore = 0){

    let formData = new FormData();
    formData.append("result", window.latestResult.result);
    formData.append("confidence", window.latestResult.confidence);
    formData.append("cdr", window.latestResult.cdr);
    formData.append("riskScore", riskScore);

    fetch("/generate_report",{
        method:"POST",
        body:formData
    })
    .then(response => response.blob())
    .then(blob => {
        let url = window.URL.createObjectURL(blob);
        let a = document.createElement("a");
        a.href = url;
        a.download = "Medical_Report.pdf";
        a.click();
    });
}
