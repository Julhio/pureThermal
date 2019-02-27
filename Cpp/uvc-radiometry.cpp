#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <iostream>
#include <queue>
#include <thread>
#include <vector>
#include <libuvc/libuvc.h>
#include "opencv2/core/core.hpp"
#include "opencv2/objdetect.hpp"
#include "opencv2/highgui.hpp"
#include "opencv2/imgproc.hpp"

#define PT_USB_VID				0x1E4E
#define PT_USB_PID				0x0100

unsigned char VS_FMT_GUID_Y16[16] = {'Y','1','6',' ', 0x00, 0x00, 0x10, 0x00, 0x80, 0x00, 0x00, 0xAA, 0x00, 0x38, 0x9b, 0x71};

using namespace std;
using namespace cv;

Mat img;
std::queue<cv::Mat> q;

/* variable declaration */
struct cb_context {
	FILE *out;
	struct timeval tv_start;
	int frames;
};

typedef std::vector<uvc_frame_desc*> fmtVector;

fmtVector *uvc_get_frame_formats_by_guid(uvc_device_handle_t *devh, unsigned char *vs_fmt_guid){
	fmtVector *fmt = new fmtVector();
	uvc_frame_desc *p_frame_desc;
	const uvc_format_desc_t *p_format_desc;
	p_format_desc = uvc_get_format_descs(devh);
	const uvc_format_desc_t *format_desc;

	while(p_format_desc != NULL)
	{
		format_desc = p_format_desc;

		if(memcmp(vs_fmt_guid, format_desc->guidFormat, 4) == 0)
		{
			p_frame_desc = format_desc->frame_descs;

			while(p_frame_desc != 0)
			{
				fmt->push_back(p_frame_desc);
				p_frame_desc = p_frame_desc->next;
			}
			return fmt;
		}
		p_format_desc = p_format_desc->next;
	}
	return {};
}

void frame_callback(uvc_frame_t *frame, void *userptr){
	Mat Img_Source16Bit_Gray(frame->height, frame->width, CV_16UC1);

	Img_Source16Bit_Gray.data = reinterpret_cast<uchar*>(frame->data);

	if(frame->data_bytes != (2 * frame->width * frame->height))
		return;

	//Check if queue is full
	/*if(q.size() > )*/ q.push(Img_Source16Bit_Gray);
}

float ktoc(float val){
	return ((val - 27315) / 100.0);
}

Mat raw_to_8bit(Mat data){
	Mat colorMat16;

	normalize(data, data, 0, 65535, NORM_MINMAX, CV_16UC1);

	Mat image_grayscale = data.clone();
	image_grayscale.convertTo(image_grayscale, CV_8UC1, 1 / 256.0);

	cvtColor(image_grayscale, colorMat16, COLOR_GRAY2RGB);

	return colorMat16;
}

void display_temperature(Mat img, double val_k, Point loc, Scalar color){
	float val = ktoc(val_k);
	char text[10];
	sprintf(text,"%.2f degC", val);
	putText(img,text, Point(loc), FONT_HERSHEY_SIMPLEX, 0.75, color, 2);
	int x, y;
	x = loc.x;
	y = loc.y;
	line(img, Point(x - 2, y), Point(x + 2, y), color, 1, LINE_4);
	line(img, Point(x, y - 2), Point(x, y + 2), color, 1, LINE_4);
}

int main(int argc, char **argv) {
	uvc_context_t *ctx;
	uvc_device_t *dev;
	uvc_device_handle_t *devh;
	uvc_stream_ctrl_t ctrl;
	uvc_error_t res;
	Mat data;
	Point minLoc, maxLoc;
	double minVal, maxVal;
	struct cb_context cb_ctx = {0};

	res = uvc_init(&ctx, NULL);	// Initialize a UVC service context.
	if (res < 0) {
		uvc_perror(res, "uvc_init");
		return res;
	}
	puts("UVC initialized");

	/* Locates the first attached UVC device, stores in dev */
	res = uvc_find_device(ctx, &dev, PT_USB_VID, PT_USB_PID, NULL);

	if (res < 0) {
		uvc_perror(res, "uvc_find_device"); /* no devices found */
	} else {
		puts("Device found");

		res = uvc_open(dev, &devh); /* Try to open the device: requires exclusive access */

		if (res < 0) {
			uvc_perror(res, "uvc_open"); /* unable to open device */
		} else {
			puts("Device opened");

			fmtVector *frame_formats = uvc_get_frame_formats_by_guid(devh, VS_FMT_GUID_Y16);

			if(sizeof(frame_formats) == 0){
				printf("device does not support Y16\n");
			} //else {

			res = uvc_get_stream_ctrl_format_size(devh, &ctrl, UVC_FRAME_FORMAT_Y16, 80, 60, 9);

			/* Print out the result */
			//uvc_print_stream_ctrl(&ctrl, stderr);

			if (res < 0) {
				uvc_perror(res, "get_mode"); /* device doesn't provide a matching stream */
			} else {

				// Start the video stream. The library will call user function callback:
				res = uvc_start_streaming(devh, &ctrl, frame_callback, &cb_ctx, 0);

				if (res < 0) {
					uvc_perror(res, "start_streaming"); /* unable to start stream */
				} else {
					puts("Streaming...");

					while(true){

						namedWindow("Lepton Radiometry", cv::WINDOW_NORMAL);
						resizeWindow("Lepton Radiometry", 640,480);

						try{
							if(!q.empty()) {
								data = q.back();
							}
							else{
								//break;
							}

							resize(data, data, Size(640,480), 0, 0, INTER_NEAREST);
							minMaxLoc(data, &minVal, &maxVal, &minLoc, &maxLoc);
							img = raw_to_8bit(data);
							display_temperature(img, minVal, minLoc, Scalar(255, 0, 0));
							display_temperature(img, maxVal, maxLoc, Scalar(0, 0, 255));

							// Display frame
							if (!img.empty()) {
								imshow("Lepton Radiometry", img);
							}
						}
						catch (exception& e){
							cout << "Standard exception: " << e.what() << endl;
						}

						// Press  ESC on keyboard to exit
						char c = waitKey(1);
						if(c==27)
							break;
					}

					destroyAllWindows();
				}
			}

			/* End the stream. Blocks until last callback is serviced */
			uvc_stop_streaming(devh);
			puts("Done streaming.");

		}
		/* Release our handle on the device */
		uvc_close(devh);
		puts("Device closed");

		/* Release the device descriptor */
		uvc_unref_device(dev);
	}
	uvc_exit(ctx);
	puts("UVC exited");

	return 0;
}

//----------------------------------------------------------------------------------
