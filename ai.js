// Simple offline AI assistant logic (handles many farmer questions)
window.Ai = {
  async ask(question, context){
    const q = question.toLowerCase();
    if(q.includes('irrig')||q.includes('water')){
      return 'Check soil moisture: if below 35% irrigate for 10-20 minutes depending on soil type. Prefer evening irrigation to reduce evaporation.';
    }
    if(q.includes('disease')||q.includes('pest')||q.includes('fung')){
      return 'High humidity and warm temperatures increase fungal risk. Inspect lower leaves, remove infected tissue, and avoid overhead watering. Consider fungicide if spread.';
    }
    if(q.includes('fertil')||q.includes('nutri')||q.includes('nitrogen')){
      return 'Apply balanced NPK during vegetative growth. For nitrogen deficiency, use urea or ammonium nitrate; follow recommended dosage per crop.';
    }
    if(q.includes('harvest')||q.includes('ready')){
      return 'Harvest timing depends on crop: check grain moisture and color for cereals, firmness/color for fruits. Monitor local market rates.';
    }
    if(q.includes('yield')||q.includes('increase')){
      return 'Improve yield by ensuring optimal irrigation, timely fertilization, pest control, and good seed varieties. Soil testing helps fine-tune fertilizer.';
    }
    return 'I recommend checking recent sensor readings (moisture, temperature, humidity). Ask specifically about irrigation, disease, fertilizer, or harvesting.';
  }
};


