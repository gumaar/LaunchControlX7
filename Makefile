deploy:
	rm -dr /Users/michalmichalik/Ableton/Ableton\ Live\ 12\ Suite.app/Contents/App-Resources/MIDI\ Remote\ Scripts/Launch_Control_XL_custom/*
	cp /Users/michalmichalik/my_space/music/ableton_python/Launch_Control_XL_custom_12/*.py /Users/michalmichalik/Ableton/Ableton\ Live\ 12\ Suite.app/Contents/App-Resources/MIDI\ Remote\ Scripts/Launch_Control_XL_custom/
copy:
	cp /Users/michalmichalik/my_space/music/ableton_python/Launch_Control_XL_custom_12/*.py /Users/michallmichalik/Ableton/Ableton\ Live\ 12\ Suite.app/Contents/App-Resources/MIDI\ Remote\ Scripts/Launch_Control_XL_custom/
log:
	tail -f ~/Library/Preferences/Ableton/Live\ 12.*/Log.txt
